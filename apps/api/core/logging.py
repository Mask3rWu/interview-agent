import logging
from logging.handlers import RotatingFileHandler

from api.core.config import LOG_DIR


def setup_logging() -> None:
    """Configure console app logs and detailed model-call file logs."""
    _setup_root_logger()
    _setup_model_loggers()


def _setup_root_logger() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    if not any(getattr(h, "_interview_agent_console", False) for h in root.handlers):
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        console._interview_agent_console = True
        root.addHandler(console)

    if not any(getattr(h, "_interview_agent_app_file", False) for h in root.handlers):
        app_file = RotatingFileHandler(
            LOG_DIR / "app.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        app_file.setLevel(logging.INFO)
        app_file.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)d - %(message)s"
        ))
        app_file._interview_agent_app_file = True
        root.addHandler(app_file)


def _setup_model_loggers() -> None:
    console_logger = logging.getLogger("model_calls.console")
    console_logger.setLevel(logging.INFO)
    console_logger.propagate = False
    if not any(getattr(h, "_interview_agent_model_console", False) for h in console_logger.handlers):
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter("LLM %(message)s"))
        console._interview_agent_model_console = True
        console_logger.addHandler(console)

    file_logger = logging.getLogger("model_calls.file")
    file_logger.setLevel(logging.INFO)
    file_logger.propagate = False
    if not any(getattr(h, "_interview_agent_model_file", False) for h in file_logger.handlers):
        model_file = RotatingFileHandler(
            LOG_DIR / "model_calls.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        model_file.setLevel(logging.INFO)
        model_file.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)d - %(message)s"
        ))
        model_file._interview_agent_model_file = True
        file_logger.addHandler(model_file)
