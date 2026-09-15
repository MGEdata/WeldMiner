"""Logging setup for workflow runs."""

from __future__ import annotations

import builtins
import io
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class LogContext:
    run_log_file: Path
    llm_log_file: Path
    llm_logger: logging.Logger


def _configure_utf8_stdio() -> None:
    if sys.platform != "win32":
        return
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    except Exception:
        pass


def _reset_logger_handlers(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def _quiet_noisy_dependencies() -> None:
    """Keep third-party import-time info logs out of workflow output."""
    for logger_name in ("smart_open", "gensim"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def setup_logging(log_dir: str | Path = "logs") -> LogContext:
    """Configure console, run-file, and LLM-call logging."""
    _configure_utf8_stdio()

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_log_file = log_path / f"run_{timestamp}.log"
    llm_log_file = log_path / f"llm_calls_{timestamp}.log"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    _reset_logger_handlers(logger)
    _quiet_noisy_dependencies()

    file_handler = logging.FileHandler(run_log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    llm_logger = logging.getLogger("llm_calls")
    llm_logger.setLevel(logging.INFO)
    llm_logger.propagate = False
    _reset_logger_handlers(llm_logger)

    llm_file_handler = logging.FileHandler(llm_log_file, encoding="utf-8")
    llm_file_handler.setLevel(logging.INFO)
    llm_file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    llm_logger.addHandler(llm_file_handler)

    def logged_print(*args, **kwargs):
        sep = kwargs.get("sep", " ")
        end = kwargs.get("end", "\n")
        message = sep.join(str(arg) for arg in args)
        if end and end != "\n":
            message = f"{message}{end}"
        logger.info(message)

    builtins.print = logged_print
    return LogContext(run_log_file=run_log_file, llm_log_file=llm_log_file, llm_logger=llm_logger)
