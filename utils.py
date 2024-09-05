import os
import logging
from paths import LOGGER_DIR
import time

def setup_logger(path, repo_id):
    # Setup path
    if not os.path.exists(path):
        os.makedirs(path)

    # Create a logger object
    logger = logging.getLogger(f"logger_{repo_id}")
    logger.setLevel(logging.DEBUG)

    # Ensure the local time is used
    formatter = logging.Formatter(
        fmt=f'%(asctime)s %(name)s %(levelname)s %(message)s (%(filename)s:%(lineno)d) ({repo_id})',
        datefmt='%m/%d/%Y %I:%M:%S %p'
    )
    formatter.converter = time.localtime

    # Create file handler
    file_handler = logging.FileHandler(os.path.join(path, f"{repo_id}.log"))
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Create stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # Silence debug messages from docker and urllib
    logging.getLogger("docker.utils.config").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    logger.info("<<<<<<<<<<<<<<<<<< Logger setup anew <<<<<<<<<<<<<<<<<<<")

    print("Successfully set up logger at path ", path)
    return logger
