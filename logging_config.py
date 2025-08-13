# logging_config.py
import logging, sys
def setup_logging():
    logger = logging.getLogger("app")
    if logger.handlers:  # 중복 방지
        return logger
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger