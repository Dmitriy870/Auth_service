import logging
import sys


def configurate_logging(level: int):
    logger = logging.getLogger()
    logger.setLevel(level)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler("../../app.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
