import logging
from pathlib import Path

LOG_PATH = Path(__file__).parent / "true_mas_debug.log"

mas_logger = logging.getLogger("true_mas")
mas_logger.setLevel(logging.DEBUG)
mas_logger.propagate = False

if not mas_logger.handlers:
    file_handler = logging.FileHandler(
        LOG_PATH,
        mode="w",
        encoding="utf-8",
    )

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )

    file_handler.setFormatter(formatter)
    mas_logger.addHandler(file_handler)