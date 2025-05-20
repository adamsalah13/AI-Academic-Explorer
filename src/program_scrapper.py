import requests
from bs4 import BeautifulSoup
import re
import json
import time
import os
import logging
from urllib.parse import urljoin
from utils.logger_config import setup_logger
from utils.html_utils import clean_text

# Get logger from configuration
logger = setup_logger("CamosunScraper")

class CamosunProgramScraper:
    """
    Scraper for Camosun College programs information.
    """
    def __init__(self, base_url="https://camosun.ca", programs_url="/programs-courses/find-program"):
        self.base_url = base_url
        self.programs_url = urljoin(base_url, programs_url)
        self.session = requests.Session()
        # Use a realistic user agent
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.programs_data = []
        
    def get_page(self, url):
        """Get page content from URL"""
        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching page {url}: {str(e)}")
            return None

    def extract_program_links(self, html_content):
        """Extract all program links from the programs listing page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        program_links = []
        
        # Look for the program listings
        views_rows = soup.select('div.views-row')
        
        for row in views_rows:
            link = row.select_one('a')
            if link and link.has_attr('href'):
                program_url = urljoin(self.base_url, link['href'])
                program_name = link.text.strip()
                program_links.append({
                    'name': program_name,
                    'url': program_url
                })
        
        return program_links

    def get_all_program_links(self):
        """Get all program links from all pages"""
        all_program_links = []
        page = 0
        more_pages = True
        
        while more_pages:
            page_url = f"{self.programs_url}?page=%2C{page}"
            logger.info(f"Fetching programs from page {page}: {page_url}")
            
            html_content = self.get_page(page_url)
            if not html_content:
                break
                
            page_links = self.extract_program_links(html_content)
            
            if not page_links:
                more_pages = False
            else:
                all_program_links.extend(page_links)
                page += 1
                # Be nice to the server
                time.sleep(1)
        
        logger.info(f"Found {len(all_program_links)} program links in total")
        return all_program_links

    def get_program_outline_details(self, program_outline_url: str, program_data: dict):
        """
        Get program outline details from the program outline page.
        """
        html_content = self.get_page(program_outline_url)
        soup = BeautifulSoup(html_content, 'lxml')

        content_div = soup.select_one('.block_content') or soup.select_one('#gateway_container') or soup.select_one('div.main') or soup   
        program_table = content_div.select_one('.program_description')
        rows = program_table.select_one('table').select('td')
        for i in range(0, len(rows), 2):
            if i + 1 < len(rows):
                # Extract the text from the first and second columns
                header = clean_text(rows[i].get_text()).lower()
                value = clean_text(rows[i + 1].get_text())

                if 'credential' in header:
                    program_data['credential'] = value
                elif 'total credits' in header:
                    program_data['total_credits'] = value
                elif 'program code' in header:
                    program_data['program_code'] = value
                elif 'cip' in header:
                    program_data['cip'] = value
        
        return program_data


    def get_program_courses(self, url):
        """
        Get all courses from a program page.
        
        Args:
            url (str): URL of the program page
            
        Returns:
            list: List of course information dictionaries with code, title, and credits if available
        """
        html_content = self.get_page(url)
        soup = BeautifulSoup(html_content, 'lxml')
        
        courses_list = soup.select('.acalog-core ul li')

        courses = []
        for element in courses_list:
        # Check if the element is a list item
            if element.name == 'li':
                # Extract the text content
                text = clean_text(element.text)
                # Look for patterns like "COURSE 101 - Course Title (3 credits)"
                course_match = re.match(r'([A-Z]{2,5}\s*\d{3,4}[A-Z]?)\s*-?\s*(.*?)(?:\s*\((\d+\.?\d*)\s*credits?\))?$', text, re.IGNORECASE)
                if course_match:
                    course_code = course_match.group(1).strip()
                    course_title = course_match.group(2).strip()
                    courses.append(f'{course_code} - {course_title}')
        return courses
    
    def extract_program_details(self, html_content, program_url):
        """Extract detailed information from a program page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        program_data = {
            "url": program_url,
            "title": "",
            "intro_text": "",
            "overview": "",
            "credential": "",
            "work_experience": "",
            "study_options": "",
            "open_to_international": "",
            "area_of_study": "",
            "length": "",
            "program_outline_url": "",
            "curriculum": {},
            #"what_you_will_learn": "",
            "tuition_info": "",
            "admission_requirements": "",
        }
        
        # Extract program title
        title_elem = soup.select_one('h1.page_title')
        if title_elem:
            program_data["title"] = title_elem.text.strip()
        
        # Extract intro text
        intro_elem = soup.select_one('div.intro-text')
        if intro_elem:
            program_data["intro_text"] = intro_elem.text.strip()
        
        # Extract program at a glance info
        glance_elements = soup.select('div.program_glance__info')
        for elem in glance_elements:
            title_elem = elem.select_one('p.info-title')
            if not title_elem:
                continue
                
            title = title_elem.text.strip().lower()
            value_elem = elem.select_one('p:not(.info-title)')
            
            if value_elem:
                value = value_elem.text.strip()
                
                if "credential" in title:
                    program_data["credential"] = value
                elif "work experience" in title:
                    program_data["work_experience"] = value
                elif "study options" in title:
                    program_data["study_options"] = value
                elif "open to international" in title:
                    program_data["open_to_international"] = value
                elif "area of study" in title:
                    program_data["area_of_study"] = value
                elif "length" in title:
                    program_data["length"] = value
        
        # Extract tab content
        # Overview tab
        overview_tab = soup.select_one('#program_tab')
        if overview_tab:
            overview_content = overview_tab.select_one('div:not(.intro-text-about):not(.image-about)')
            if overview_content:
                program_data["overview"] = overview_content.text.strip()
        
        # What you'll learn tab
        learn_tab = soup.select_one('#more_tab')
        if learn_tab:
            learn_content = learn_tab.select_one('div:not(.intro-text-about):not(.image-about)')
            program_outline_link = None
            if learn_content:
                # Find the program outline button link if it exists
                outline_button = learn_content.select_one('a.button.cta_button')
                if outline_button and outline_button.has_attr('href'):
                    program_outline_link = urljoin(self.base_url, outline_button['href'])
                    program_data["program_outline_url"] = program_outline_link
                    program_data["curriculum"] = self.get_program_courses(program_outline_link)
                    program_data = self.get_program_outline_details(program_outline_link, program_data)
        
        # Tuition tab
        money_tab = soup.select_one('#money_tab')
        if money_tab:
            program_data["tuition_info"] = money_tab.text.strip()
        
        # Admission tab
        admission_tab = soup.select_one('#admission_tab')
        if admission_tab:
            program_data["admission_requirements"] = admission_tab.text.strip()
        
        return program_data
    
    def scrape_program(self, program_link):
        """Scrape detailed info for a single program"""
        logger.info(f"Scraping program: {program_link['name']}")
        
        html_content = self.get_page(program_link['url'])
        if not html_content:
            return None
        
        program_data = self.extract_program_details(html_content, program_link['url'])
        # Add name from the program list for consistency
        #program_data["name"] = program_link['name']
        
        return program_data

    def scrape_all_programs(self):
        """Scrape all programs"""
        # Get all program links
        program_links = self.get_all_program_links()
        
        for i, program_link in enumerate(program_links):
            try:
                logger.info(f"Processing program {i+1}/{len(program_links)}: {program_link['name']}")
                
                # Check if we already have data for this program
                program_data = self.scrape_program(program_link)
                
                if program_data:
                    self.programs_data.append(program_data)
                
                # Be nice to the server
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error processing program {program_link['name']}: {str(e)}")
        
        return self.programs_data
    
    def save_to_json(self, filename="camosun_programs.json"):
        """Save scraped data to a JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.programs_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Data saved to {filename}")
        
        return filename


def main():
    from utils.file_utils import ensure_directory_exists
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    ensure_directory_exists(output_dir)
    
    # Initialize and run the scraper
    scraper = CamosunProgramScraper()
    scraper.scrape_all_programs()
    
    # Save the data
    output_file = os.path.join(output_dir, "camosun_programs.json")
    scraper.save_to_json(output_file)
    logger.info(f"Scraping completed. Data saved to {output_file}")

if __name__ == "__main__":
    main()