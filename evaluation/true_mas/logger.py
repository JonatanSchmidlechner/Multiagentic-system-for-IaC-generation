import logging
from pathlib import Path
from datetime import datetime

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_PATH = LOG_DIR / f"true_mas_debug_{timestamp}.log"

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