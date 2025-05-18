"""
HTML parsing utilities for the scraper
"""

import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)

def clean_text(text):
    """
    Clean text by removing extra whitespace and normalizing line breaks
    
    Args:
        text (str): Text to clean
    
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
        
    # Replace multiple whitespace with single space
    text = re.sub(r'\s+', ' ', text)
    # Replace multiple newlines with single newline
    text = re.sub(r'\n+', '\n', text)
    # Strip leading/trailing whitespace
    return text.strip()

def extract_text_from_element(element):
    """
    Extract clean text from a BeautifulSoup element
    
    Args:
        element (BeautifulSoup): HTML element to extract text from
    
    Returns:
        str: Cleaned text or empty string if element is None
    """
    if not element:
        return ""
        
    return clean_text(element.get_text())

def get_absolute_url(base_url, relative_url):
    """
    Convert a relative URL to an absolute URL
    
    Args:
        base_url (str): Base URL
        relative_url (str): Relative or absolute URL
    
    Returns:
        str: Absolute URL
    """
    if not relative_url:
        return None
        
    # Check if URL is already absolute
    if bool(urlparse(relative_url).netloc):
        return relative_url
        
    # Join base URL and relative URL
    return urljoin(base_url, relative_url)

def extract_table_as_dict(table_element):
    """
    Extract HTML table data as a list of dictionaries
    
    Args:
        table_element (BeautifulSoup): HTML table element
    
    Returns:
        list: List of dictionaries with column names as keys and cell values as values
    """
    if not table_element:
        return []
        
    data = []
    headers = []
    
    # Extract header row
    header_row = table_element.find('thead')
    if header_row:
        header_cells = header_row.find_all('th')
        headers = [extract_text_from_element(cell) for cell in header_cells]
    
    # If no headers found, use first row as headers
    if not headers:
        first_row = table_element.find('tr')
        if first_row:
            header_cells = first_row.find_all(['th', 'td'])
            headers = [extract_text_from_element(cell) for cell in header_cells]
            # Skip first row in data extraction
            rows = table_element.find_all('tr')[1:]
        else:
            return []
    else:
        rows = table_element.find_all('tr')
    
    # Extract data rows
    for row in rows:
        cells = row.find_all('td')
        if not cells:
            continue
            
        row_data = {}
        for i, cell in enumerate(cells):
            if i < len(headers):
                header = headers[i]
                row_data[header] = extract_text_from_element(cell)
        
        if row_data:
            data.append(row_data)
    
    return data
