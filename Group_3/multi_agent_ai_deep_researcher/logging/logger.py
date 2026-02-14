"""
Structured logging setup for Multi-Agent AI Deep Researcher.

Provides JSON-formatted structured logging with correlation IDs, agent context,
and execution tracing. Supports both JSON and text formats.

Usage:
    from logging.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("Starting research", extra={
        "session_id": "sess_123",
        "agent": "retriever",
        "step": 1
    })
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from config import settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""
    
    def __init__(self, use_json: bool = True):
        """
        Initialize the structured formatter.
        
        Args:
            use_json: If True, output JSON format; otherwise plain text.
        """
        self.use_json = use_json
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record into JSON or text.
        
        Args:
            record: The log record to format.
        
        Returns:
            Formatted log string (JSON or text).
        """
        if self.use_json:
            return self._format_json(record)
        return self._format_text(record)
    
    def _format_json(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with all context."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line_number": record.lineno,
        }
        
        # Add extra fields from the log record
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        if hasattr(record, "agent"):
            log_data["agent"] = record.agent
        if hasattr(record, "step"):
            log_data["step"] = record.step
        if hasattr(record, "iteration"):
            log_data["iteration"] = record.iteration
        if hasattr(record, "execution_time_ms"):
            log_data["execution_time_ms"] = record.execution_time_ms
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }
        
        # Add any additional context
        if hasattr(record, "context") and isinstance(record.context, dict):
            log_data["context"] = record.context
        
        try:
            return json.dumps(log_data)
        except (TypeError, ValueError) as e:
            # Fallback if JSON serialization fails
            log_data["message"] = f"JSON serialization error: {str(e)}"
            return json.dumps(log_data)
    
    def _format_text(self, record: logging.LogRecord) -> str:
        """Format log record as human-readable text."""
        # Build the basic message
        basic_format = f"[{record.levelname}] {record.name}"
        
        # Add context if available
        context_parts = []
        if hasattr(record, "session_id"):
            context_parts.append(f"sess={record.session_id}")
        if hasattr(record, "agent"):
            context_parts.append(f"agent={record.agent}")
        if hasattr(record, "step"):
            context_parts.append(f"step={record.step}")
        if hasattr(record, "iteration"):
            context_parts.append(f"iter={record.iteration}")
        if hasattr(record, "execution_time_ms"):
            context_parts.append(f"time={record.execution_time_ms}ms")
        
        if context_parts:
            basic_format += f" ({', '.join(context_parts)})"
        
        basic_format += f": {record.getMessage()}"
        
        # Add exception if present
        if record.exc_info:
            basic_format += f"\n{self.formatException(record.exc_info)}"
        
        return basic_format


class LoggerAdapter(logging.LoggerAdapter):
    """
    Custom adapter to add context information to log records.
    
    Allows passing context like session_id, agent name, step number, etc.
    to all log calls without needing to pass them every time.
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process log message and add context."""
        # The extra dict is already handled by LoggerAdapter
        return msg, kwargs
    
    def info_with_context(
        self,
        msg: str,
        session_id: Optional[str] = None,
        agent: Optional[str] = None,
        step: Optional[int] = None,
        iteration: Optional[int] = None,
        execution_time_ms: Optional[float] = None,
        **kwargs
    ):
        """Log info with context information."""
        extra = {}
        if session_id:
            extra["session_id"] = session_id
        if agent:
            extra["agent"] = agent
        if step is not None:
            extra["step"] = step
        if iteration is not None:
            extra["iteration"] = iteration
        if execution_time_ms is not None:
            extra["execution_time_ms"] = execution_time_ms
        extra.update(kwargs)
        
        self.info(msg, extra=extra)
    
    def error_with_context(
        self,
        msg: str,
        session_id: Optional[str] = None,
        agent: Optional[str] = None,
        step: Optional[int] = None,
        **kwargs
    ):
        """Log error with context information."""
        extra = {}
        if session_id:
            extra["session_id"] = session_id
        if agent:
            extra["agent"] = agent
        if step is not None:
            extra["step"] = step
        extra.update(kwargs)
        
        self.error(msg, extra=extra, exc_info=True)
    
    def debug_with_context(
        self,
        msg: str,
        session_id: Optional[str] = None,
        agent: Optional[str] = None,
        **kwargs
    ):
        """Log debug with context information."""
        extra = {}
        if session_id:
            extra["session_id"] = session_id
        if agent:
            extra["agent"] = agent
        extra.update(kwargs)
        
        self.debug(msg, extra=extra)


def setup_logging() -> None:
    """
    Configure logging for the entire application.
    
    Sets up both console and file logging with appropriate formatters.
    Called once at application startup.
    """
    # Get root logger
    root_logger = logging.getLogger()
    
    # Set log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers
    root_logger.handlers = []
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    use_json = settings.log_format.lower() == "json"
    console_handler.setFormatter(StructuredFormatter(use_json=use_json))
    root_logger.addHandler(console_handler)
    
    # File handler (optional, if LOG_FILE env var is set)
    log_file = Path("./logs")
    if log_file.exists() or settings.is_production:
        log_file.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file / "research.log")
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_handler.setFormatter(StructuredFormatter(use_json=use_json))
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__).
    
    Returns:
        Logger instance configured for the application.
    
    Example:
        logger = get_logger(__name__)
        logger.info("Starting process")
    """
    logger = logging.getLogger(name)
    return logger


def get_logger_with_context(name: str) -> LoggerAdapter:
    """
    Get a logger adapter with context support.
    
    This is useful for agents and long-running processes where you want
    to attach session_id, agent name, etc. to all logs from a component.
    
    Args:
        name: Logger name (typically __name__).
    
    Returns:
        LoggerAdapter instance with context support.
    
    Example:
        logger = get_logger_with_context(__name__)
        logger.info_with_context(
            "Query processed",
            session_id="sess_123",
            agent="retriever",
            step=1
        )
    """
    logger = logging.getLogger(name)
    adapter = LoggerAdapter(logger, {})
    return adapter


__all__ = [
    "setup_logging",
    "get_logger",
    "get_logger_with_context",
    "StructuredFormatter",
    "LoggerAdapter",
]
