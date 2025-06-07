import logging
from colorlog import ColoredFormatter


class KeywordColoredFormatter(ColoredFormatter):
    """Color messages based on keywords as well as log level."""

    def __init__(self, *args, keyword_colors=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyword_colors = {k.lower(): v for k, v in (keyword_colors or {}).items()}

    def format(self, record):
        msg = record.getMessage().lower()
        for keyword, color in self.keyword_colors.items():
            if keyword in msg:
                record.log_color = color
                break
        return super().format(record)


def setup_logging(level=logging.INFO):
    handler = logging.StreamHandler()
    formatter = KeywordColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "white",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
        keyword_colors={
            "delete": "red",
            "insert": "green",
            "incoming": "blue",
            "outgoing": "cyan",
        },
    )
    handler.setFormatter(formatter)
    logging.basicConfig(level=level, handlers=[handler])

