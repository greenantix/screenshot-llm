#!/usr/bin/env python3
"""
Logger utility for Screenshot LLM Assistant
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional
import traceback

def get_logger(name: str = None) -> logging.Logger:
    """Get a configured logger instance"""
    if name is None:
        name = __name__
    
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure logger
        logger.setLevel(logging.DEBUG)
        
        # File handler
        file_handler = logging.FileHandler(log_dir / "screenshot-llm-gui.log")
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

def log_exception(exception: Exception, context: str = "", logger_name: str = None):
    """Log an exception with full traceback"""
    logger = get_logger(logger_name)
    
    error_msg = f"{context}: {str(exception)}" if context else str(exception)
    logger.error(error_msg)
    logger.debug(traceback.format_exc())

if __name__ == "__main__":
    # Test the logger
    logger = get_logger()
    logger.info("Logger test successful")
    
    try:
        raise ValueError("Test exception")
    except Exception as e:
        log_exception(e, "Testing exception logging")