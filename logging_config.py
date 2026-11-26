import logging
import os

# Create logs directory
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    filename="logs/pipeline.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8"
)

logger = logging.getLogger("EcommercePipeline")


def log_start(stage):
    logger.info(f"{stage} - Started")


def log_success(stage, rows=None):
    logger.info(f"{stage} - Completed successfully | Rows: {rows}")


def log_error(stage, error):
    logger.error(f"{stage} - Failed | Error: {error}")