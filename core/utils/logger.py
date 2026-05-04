import logging
import os

def get_data_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger that writes to data_fetch.log in the project root.
    """
    logger = logging.getLogger(name)
    
    # Only configure if it doesn't already have handlers to prevent duplicate logs
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # File Handler
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        log_file = os.path.join(project_root, "data_fetch.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        
        # Add console handler so we still see it in the terminal
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger
