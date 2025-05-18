"""
Utility modules for the University Scraper project
"""

from .logger_config import setup_logger
from .file_utils import ensure_directory_exists, clean_directory, backup_file
from .html_utils import clean_text, extract_text_from_element, get_absolute_url, extract_table_as_dict

__all__ = [
    'setup_logger',
    'ensure_directory_exists',
    'clean_directory',
    'backup_file',
    'clean_text',
    'extract_text_from_element',
    'get_absolute_url',
    'extract_table_as_dict',
]
