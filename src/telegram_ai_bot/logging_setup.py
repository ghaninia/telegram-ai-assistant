"""Application logging: rotating file in the data directory plus stderr."""

import logging
from logging.handlers import RotatingFileHandler

from telegram_ai_bot import paths


def configure_logging(level: int = logging.INFO) -> None:
    formatter = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")

    file_handler = RotatingFileHandler(
        paths.log_dir() / "app.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers[:] = [file_handler, console_handler]
    # requests/urllib3 are noisy at INFO.
    logging.getLogger("urllib3").setLevel(logging.WARNING)
