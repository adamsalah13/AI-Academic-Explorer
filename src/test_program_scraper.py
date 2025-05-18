#!/usr/bin/env python3
"""
Test Program Scraper

This script tests the program scraper on a single program URL to validate
the parsing logic before running it on the full catalog.
"""

import json
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from old_program_scraper import get_soup, extract_program_details

# Constants
BASE_URL = "https://calendar.camosun.ca/"
TEST_PROGRAM_URL = "https://calendar.camosun.ca/preview_program.php?catoid=25&poid=3954&returnto=2225"

def main():
    """Test scraper on a single program page."""
    print(f"Testing scraper on: {TEST_PROGRAM_URL}")
    
    # Create a mock program object to pass to extract_program_details
    mock_program = {
        'title': 'Test Program',
        'url': TEST_PROGRAM_URL
    }
    
    # Extract details from the test program
    program_details = extract_program_details(mock_program)
    
    # Print the extracted details in a readable format
    print("\nExtracted Program Details:")
    print(json.dumps(program_details, indent=2, ensure_ascii=False))
    
    # Print specific curriculum info
    print("\nCurriculum Courses:")
    if program_details['curriculum']:
        for i, course in enumerate(program_details['curriculum'], 1):
            print(f"{i}. {course['code']} - {course['title']} ({course['credits']} credits)")
    else:
        print("No curriculum information found. Check your selector patterns.")
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()