import logging
import sys
from datetime import datetime
import os

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class LoggerFactory:
    """Factory class to create and configure loggers."""
    
    @staticmethod
    def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
        """
        Create and configure a logger instance.
        
        Args:
            name: Name of the logger
            level: Logging level (default: INFO)
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Avoid adding handlers if they already exist
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
            logger.addHandler(console_handler)
            
            # File handler with daily rotation
            today = datetime.now().strftime("%Y-%m-%d")
            file_handler = logging.FileHandler(f"logs/{name}_{today}.log")
            file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
            logger.addHandler(file_handler)
        
        return logger


# Application loggers
app_logger = LoggerFactory.get_logger("app")
api_logger = LoggerFactory.get_logger("api")
db_logger = LoggerFactory.get_logger("db")
auth_logger = LoggerFactory.get_logger("auth")