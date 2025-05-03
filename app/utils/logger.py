import logging
import sys

# Configure the logger
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=log_format, stream=sys.stdout)

# Create a logger instance
logger = logging.getLogger(__name__)

# Example usage (optional, can be removed if not needed)
if __name__ == "__main__":
    logger.info("Logger initialized successfully.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
