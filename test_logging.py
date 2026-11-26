from logging_config import logger, log_start, log_success, log_error

log_start("Silver Loading")

try:
    rows_loaded = 18484

    log_success("Silver Loading", rows_loaded)

except Exception as e:
    log_error("Silver Loading", e)