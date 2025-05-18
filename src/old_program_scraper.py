#!/usr/bin/env python3
"""
Program Scraper for Camosun College

This script scrapes program information from the Camosun College website
and stores it in a JSON file for later importing into a Neo4j database.
"""

import os
import json
import re
import requests
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
from datetime import datetime
from urllib.parse import urljoin

# Constants
BASE_URL = "https://calendar.camosun.ca/"
PROGRAMS_LIST_URL = "https://calendar.camosun.ca/content.php?catoid=25&navoid=2225"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"programs_data_{datetime.now().strftime('%Y%m%d')}.json")

# Ensure data directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_soup(url):
    """Get BeautifulSoup object from URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'lxml')

def extract_program_links():
    """Extract all program links from the programs listing page."""
    print("Fetching program links...")
    soup = get_soup(PROGRAMS_LIST_URL)
    
    program_links = []
    
    # Look for all links on the page that point to program pages
    for link in soup.select('a[href*="preview_program.php"]'):
        href = link.get('href', '')
        if href and 'preview_program.php' in href:
            program_links.append({
                'title': link.text.strip(),
                'url': urljoin(BASE_URL, href)
            })
    
    print(f"Found {len(program_links)} programs")
    return program_links

def clean_text(text):
    """Clean up text by removing extra whitespace and normalizing line breaks."""
    if not text:
        return ""
    
    # Replace multiple spaces and line breaks with a single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_program_details(program):
    """Extract detailed information about a program from its page."""
    url = program['url']
    print(f"Scraping: {program['title']}")
    soup = get_soup(url)
    
    # Initialize program details dictionary
    details = {
        'title': program['title'],
        'url': url,
        'overview': '',
        'credential': '',
        'total_credits': '',
        'length': '',
        'location': '',
        'start_date': '',
        'curriculum': [],
        'admission_requirements': '',
        'program_outline': '',
        'contact': '',
        'metadata': {},
    }
    
    # Extract main content area - try different possible containers
    content_div = soup.select_one('.block_content') or soup.select_one('#gateway_container') or soup.select_one('div.main') or soup
    
    # Extract program overview
    # Look for various headings that might contain overview information
    overview_headings = ['Overview']
    for heading in overview_headings:
        header = content_div.find(['h2', 'h3'], text=re.compile(f'{heading}', re.IGNORECASE))
        if header:
            overview_text = ""
            for elem in header.next_siblings:
                if elem.name in ['h2', 'h3', 'h4']:
                    break
                if elem.name == 'p' or (elem.name == 'div' and not elem.select('table')):
                    overview_text += clean_text(elem.text) + "\n"
            if overview_text:
                details['overview'] = overview_text.strip()
                break
    
    # Extract program details from tables
    # Look for tables containing program metadata
    program_tables = content_div.select('table.sc_plangrid') or content_div.select('table.datadisplaytable')
    for table in program_tables:
        rows = table.select('tr')
        for row in rows:
            cells = row.select('td')
            if len(cells) >= 2:
                header = clean_text(cells[0].text).lower()
                value = clean_text(cells[1].text)
                
                if 'Credential' in header:
                    details['credential'] = value
                elif 'Total Credits' in header:
                    details['total_credits'] = value
                elif 'length' in header:
                    details['length'] = value
                elif 'location' in header:
                    details['location'] = value
                elif 'start' in header:
                    details['start_date'] = value
                else:
                    # Store other metadata
                    details['metadata'][header] = value
    
    # Extract curriculum - this is especially important for your requirements
    curriculum_section = None
    
    # Look for curriculum heading
    for heading in ['Curriculum', 'Program Content', 'Courses']:
        curriculum_section = content_div.find(['h2', 'h3', 'h4'], text=re.compile(f'{heading}', re.IGNORECASE))
        if curriculum_section:
            break
    
    if curriculum_section:
        # Look for tables after the curriculum heading
        next_elem = curriculum_section.next_sibling
        while next_elem:
            if next_elem.name == 'table':
                # Process this table as curriculum
                for row in next_elem.select('tr')[1:]:  # Skip header row
                    cells = row.select('td')
                    if len(cells) >= 2:
                        course = {
                            'code': clean_text(cells[0].text),
                            'title': clean_text(cells[1].text),
                        }
                        
                        # Credits might be in the third column
                        if len(cells) > 2:
                            credits_text = clean_text(cells[2].text)
                            # Try to extract just the number
                            credit_match = re.search(r'(\d+\.?\d*)', credits_text)
                            course['credits'] = credit_match.group(1) if credit_match else credits_text
                        
                        details['curriculum'].append(course)
                break
            
            # Also check for structured lists that might contain curriculum
            if next_elem.name in ['ul', 'ol']:
                for li in next_elem.select('li'):
                    # Try to parse list items as courses
                    text = clean_text(li.text)
                    # Look for patterns like "COURSE 101 - Course Title (3 credits)"
                    course_match = re.match(r'([A-Z]{2,5}\s*\d{3,4}[A-Z]?)\s*-?\s*(.*?)(?:\s*\((\d+\.?\d*)\s*credits?\))?$', text, re.IGNORECASE)
                    if course_match:
                        course = {
                            'code': course_match.group(1).strip(),
                            'title': course_match.group(2).strip(),
                            'credits': course_match.group(3) if course_match.group(3) else ''
                        }
                        details['curriculum'].append(course)
                break
            
            # If we hit another heading, stop looking
            if next_elem.name in ['h2', 'h3', 'h4']:
                break
                
            next_elem = next_elem.next_sibling
    
    # If no curriculum found yet, try to find any tables with course-like info
    if not details['curriculum']:
        for table in content_div.select('table'):
            has_course_data = False
            for row in table.select('tr'):
                cells = row.select('td')
                if len(cells) >= 2:
                    text = clean_text(cells[0].text)
                    # Check if first cell looks like a course code
                    if re.match(r'^[A-Z]{2,5}\s*\d{3,4}[A-Z]?$', text, re.IGNORECASE):
                        has_course_data = True
                        break
            
            if has_course_data:
                for row in table.select('tr')[1:]:  # Skip header row
                    cells = row.select('td')
                    if len(cells) >= 2:
                        course = {
                            'code': clean_text(cells[0].text),
                            'title': clean_text(cells[1].text),
                        }
                        
                        # Credits might be in the third column
                        if len(cells) > 2:
                            credits_text = clean_text(cells[2].text)
                            # Try to extract just the number
                            credit_match = re.search(r'(\d+\.?\d*)', credits_text)
                            course['credits'] = credit_match.group(1) if credit_match else credits_text
                        
                        details['curriculum'].append(course)
    
    # Extract admission requirements
    admission_section = content_div.find(['h2', 'h3', 'h4'], text=re.compile('Admission Requirements', re.IGNORECASE))
    if admission_section:
        admission_text = ""
        for elem in admission_section.next_siblings:
            if elem.name in ['h2', 'h3', 'h4']:
                break
            if elem.name in ['p', 'ul', 'ol', 'div'] and not elem.select('table'):
                admission_text += clean_text(elem.text) + "\n"
        details['admission_requirements'] = admission_text.strip()
    
    # Extract program contact information
    contact_section = content_div.find(['h2', 'h3', 'h4'], text=re.compile('Contact', re.IGNORECASE))
    if contact_section:
        contact_text = ""
        for elem in contact_section.next_siblings:
            if elem.name in ['h2', 'h3', 'h4']:
                break
            if elem.name in ['p', 'div', 'address']:
                contact_text += clean_text(elem.text) + "\n"
        details['contact'] = contact_text.strip()
    
    return details

def main():
    """Main function to orchestrate the scraping process."""
    program_links = extract_program_links()
    
    all_programs = []
    for program in tqdm(program_links, desc="Scraping programs"):
        try:
            program_details = extract_program_details(program)
            all_programs.append(program_details)
            # Be nice to the server
            time.sleep(1)
        except Exception as e:
            print(f"Error scraping {program['title']}: {str(e)}")
    
    # Save data to JSON file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_programs, f, indent=2, ensure_ascii=False)
    
    print(f"Scraped {len(all_programs)} programs. Data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()