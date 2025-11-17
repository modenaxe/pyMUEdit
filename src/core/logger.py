import logging
import os

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "app.log")

# Option to enable/disable console logging
ENABLE_CONSOLE_LOG = False

# Create logger
logger = logging.getLogger("core")
logger.setLevel(logging.DEBUG)  # log everything DEBUG and above

# File handler (always logs DEBUG+ to file)
file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Optional console handler
if ENABLE_CONSOLE_LOG:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # console logs INFO+ by default
    console_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)