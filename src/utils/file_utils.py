"""
File and directory utility functions
"""

import os
import shutil
import logging

logger = logging.getLogger(__name__)

def ensure_directory_exists(directory_path):
    """
    Create directory if it doesn't exist
    
    Args:
        directory_path (str): Path to directory
    
    Returns:
        str: Path to the directory
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        logger.info(f"Created directory: {directory_path}")
    return directory_path

def clean_directory(directory_path, exclude=None):
    """
    Clean a directory by removing all files and subdirectories except those specified
    
    Args:
        directory_path (str): Path to directory to clean
        exclude (list, optional): List of filenames to exclude from cleaning
    
    Returns:
        bool: True if successful, False otherwise
    """
    exclude = exclude or []
    
    if not os.path.exists(directory_path):
        logger.warning(f"Directory does not exist: {directory_path}")
        return False
    
    try:
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            
            if item in exclude:
                continue
                
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
                
        logger.info(f"Cleaned directory: {directory_path}")
        return True
    except Exception as e:
        logger.error(f"Error cleaning directory {directory_path}: {str(e)}")
        return False

def backup_file(file_path, backup_dir=None):
    """
    Create a backup copy of a file
    
    Args:
        file_path (str): Path to file to backup
        backup_dir (str, optional): Directory to store backup. If None, stores in same directory with .bak extension
        
    Returns:
        str: Path to backup file if successful, None otherwise
    """
    if not os.path.exists(file_path):
        logger.warning(f"File does not exist: {file_path}")
        return None
    
    try:
        if backup_dir:
            ensure_directory_exists(backup_dir)
            filename = os.path.basename(file_path)
            backup_path = os.path.join(backup_dir, filename + ".bak")
        else:
            backup_path = file_path + ".bak"
            
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Error backing up file {file_path}: {str(e)}")
        return None
