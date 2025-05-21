import requests
from bs4 import BeautifulSoup
import re
import json
import time
import os
import logging
import traceback
from urllib.parse import urljoin, parse_qs
from utils.logger_config import setup_logger
# Get logger from configuration
logger = setup_logger("CamosunCourseScraper")

class CamosunCourseScraper:
    """
    Scraper for Camosun College course information from the academic calendar.
    """
    def __init__(self, base_url="https://calendar.camosun.ca", 
                 courses_url="/content.php?catoid=25&navoid=2223"):
        self.base_url = base_url
        self.courses_url = urljoin(base_url, courses_url)
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.courses_data = []
        
    def get_page(self, url):
        """Get page content from URL"""
        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching page {url}: {str(e)}")
            return None

    def extract_course_links(self, html_content):
        """Extract all course links from the course listing page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        course_links = []
        
        # Look for course links in the table
        course_rows = soup.select('td.width a[href*="preview_course"]')
        
        for link in course_rows:
            if link.has_attr('href'):
                # extract coid from the onclick string
                course_coid = link['onclick'].split(',')[1].strip().replace("'", "")
                href_link = f'preview_course_nopop.php?catoid=25&coid={course_coid}'
                course_url = urljoin(self.base_url, href_link)
                course_code = link.text.strip()
                course_links.append({
                    'code': course_code,
                    'url': course_url
                })
        
        return course_links
    

    def extract_course_details(self, html_content, course_url):
        """Extract detailed information from a course page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        course_data = {
            "url": course_url,
            "code": "",
            "title": "",
            "description": "",
            "credits": "",
            "hours": "",
            "Prerequisites": "",
            "Equivalencies": "",
            "Pre or Co-requisites": ""
        }

        # Extract course title and code
        title_elem = soup.select_one('#course_preview_title')
        if title_elem:
            title_parts = title_elem.text.split('-')
            if len(title_parts) == 2:
                course_data["code"] = title_parts[0].strip()
                course_data["title"] = title_parts[1].strip()
        
        # Extract course details from the content
        content = soup.select_one('td.block_content')
        if content:
            # Extract course description
            text_list = content.find('p').find_all(string=True)
            course_description = max(text_list, key=len)
            course_data["description"] = course_description
            # Extract course prerequisites list if exists
            li_list = content.select('li')
            if li_list:
                prereq_list = []
                for li_elem in li_list:
                    prereq_list.append(li_elem.text.strip().replace('\xa0', ' '))

                if 'Equivalencies' in text_list:
                    course_data['Equivalencies'] = prereq_list
                    
                elif 'Pre or Co-requisites' in text_list:
                    prereq_dict = {}
                    list_key = text_list[text_list.index('Pre or Co-requisites') + 1].strip().replace(':', '')
                    prereq_dict[list_key] = prereq_list
                    course_data['Pre or Co-requisites'] = prereq_dict
                elif 'Prerequisites' in text_list:
                    prereq_dict = {}
                    list_key = text_list[text_list.index('Prerequisites') + 1].strip().replace(':', '')
                    prereq_dict[list_key] = prereq_list
                    course_data['Prerequisites'] = prereq_dict

            # Extract credits and hours
            for strong_tag in content.find_all('strong'):
                label = strong_tag.text.strip().lower()
                value = strong_tag.next_sibling
                if value:
                    value = value.strip()
                    
                    if "credit" in label:
                        course_data["credits"] = value
                    elif "hour" in label:
                        course_data["hours"] = value
        
        return course_data

    def scrape_course(self, course_link):
        """Scrape detailed info for a single course"""
        logger.info(f"Scraping course: {course_link['code']}")
        
        html_content = self.get_page(course_link['url'])
        if not html_content:
            return None
        
        course_data = self.extract_course_details(html_content, course_link)
        return course_data

    def scrape_all_courses(self):
        """Scrape all courses from all paginated course listing pages"""
        all_course_links = []

        # First page (special URL)
        logger.info("Scraping first course page...")
        first_page_content = self.get_page(self.courses_url)
        if first_page_content:
            all_course_links.extend(self.extract_course_links(first_page_content))
        else:
            logger.error("Failed to fetch the first course page.")

        # Check how many pagination pages exist
        # Use one of the paginated URLs to find the total number of pages
        paginated_base_url = (
            "https://calendar.camosun.ca/content.php?"
            "catoid=25&catoid=25&navoid=2223&filter%5Bitem_type%5D=3&"
            "filter%5Bonly_active%5D=1&filter%5B3%5D=1&filter%5Bcpage%5D={page}#acalog_template_course_filter"
        )

        # Start from page 2 — first was already done
        for page in range(2, 14):  # Use a high number and break when no content
            page_url = paginated_base_url.format(page=page)
            logger.info(f"Scraping page {page}: {page_url}")
            page_content = self.get_page(page_url)

            if not page_content:
                logger.info(f"No content found on page {page}. Assuming last page reached.")
                break

            links = self.extract_course_links(page_content)
            if not links:
                logger.info(f"No courses found on page {page}. Ending pagination.")
                break

            all_course_links.extend(links)
            time.sleep(1)  # Be polite

        logger.info(f"Total courses found: {len(all_course_links)}")

        # Now scrape each course
        for i, course_link in enumerate(all_course_links):
            try:
                logger.info(f"Processing course {i + 1}/{len(all_course_links)}: {course_link['code']}")
                course_data = self.scrape_course(course_link)
                if course_data:
                    self.courses_data.append(course_data)
                time.sleep(2)  # Be nice to the server
            except Exception as e:
                logger.error(f"Error processing course {course_link['code']}: {str(e)}")
                logger.error("Full traceback:\n" + traceback.format_exc())

        return self.courses_data
    
    def save_to_json(self, filename="camosun_courses.json"):
        """Save scraped data to a JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.courses_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Data saved to {filename}")
        
        return filename

def main():
    from utils.file_utils import ensure_directory_exists
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    ensure_directory_exists(output_dir)
    
    # Initialize and run the scraper
    scraper = CamosunCourseScraper()
    scraper.scrape_all_courses()
    
    # Save the data
    output_file = os.path.join(output_dir, "camosun_courses.json")
    scraper.save_to_json(output_file)
    logger.info(f"Scraping completed. Data saved to {output_file}")

if __name__ == "__main__":
    main()
