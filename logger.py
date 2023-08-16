import logging
from logging.handlers import RotatingFileHandler
import os
import datetime

# Create a logger
logger = logging.getLogger('Umbrella')
logger.setLevel(logging.INFO)

# Create a log formatter
log_format = '[%(asctime)s] Umbrella - %(message)s'
formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')

# Create a file handler with rotation
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f'log_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
handler = RotatingFileHandler(log_file, maxBytes=1000000, backupCount=3, encoding='utf-8')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
