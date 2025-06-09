import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

def setup_logger(log_dir: str = "logs") -> logging.Logger:
    """Set up and configure the application logger"""
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("ScreenshotLLM")
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handlers
    debug_handler = logging.FileHandler(
        log_path / "debug.log",
        encoding='utf-8'
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(file_formatter)
    
    error_handler = logging.FileHandler(
        log_path / "error.log",
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(debug_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger

# Global logger instance
_logger: Optional[logging.Logger] = None

def get_logger() -> logging.Logger:
    """Get or create the global logger instance"""
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger

def log_exception(e: Exception, context: Optional[str] = None):
    """Convenience function to log exceptions"""
    logger = get_logger()
    if context:
        logger.error(f"{context}: {str(e)}", exc_info=True)
    else:
        logger.error(str(e), exc_info=True)