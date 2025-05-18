"""
Logger configuration utilities for the scraper
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_level=logging.INFO, log_file=None):
    """
    Set up and return a logger with the given name and level.
    
    Args:
        name (str): Name of the logger
        log_level (int): Logging level (default: logging.INFO)
        log_file (str, optional): Path to log file. If None, logs will only go to console.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.propagate = False  # Don't propagate to parent loggers
    
    # Remove existing handlers if any
    if logger.handlers:
        logger.handlers = []
    
    # Create console handler with formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add console handler to logger
    logger.addHandler(console_handler)
    
    # If log file specified, also log to file
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Create file handler which logs even debug messages
        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
