"""
Structured logging module for Money Minder Chatbot.

Provides JSON-based structured logging for queries, responses, tool execution,
and errors with support for log rotation and multiple output handlers.
"""

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import traceback
import time


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add event-specific data if present
        if hasattr(record, "event_type"):
            log_data["event_type"] = getattr(record, "event_type")

        if hasattr(record, "event_data"):
            log_data["data"] = getattr(record, "event_data")

        if hasattr(record, "session_id"):
            log_data["session_id"] = getattr(record, "session_id")

        if hasattr(record, "query_id"):
            log_data["query_id"] = getattr(record, "query_id")

        # Add exception info if present
        if record.exc_info:
            exc_type = record.exc_info[0]
            exc_value = record.exc_info[1]
            exception_data: Dict[str, Any] = {
                "type": exc_type.__name__ if exc_type else None,
                "message": str(exc_value) if exc_value else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }
            log_data["exception"] = exception_data

        return json.dumps(log_data, default=str)


class StructuredLogger:
    """Structured logger with specialized methods for different event types"""

    def __init__(
        self,
        name: str = "money_minder",
        log_dir: str = "logs",
        log_file: str = "app.log",
        log_level: str = "INFO",
        log_to_console: bool = True,
        log_to_file: bool = True,
        rotation_size_mb: int = 10,
        retention_days: int = 30,
    ):
        """
        Initialize structured logger

        Args:
            name: Logger name
            log_dir: Directory for log files
            log_file: Main log file name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_console: Enable console logging
            log_to_file: Enable file logging
            rotation_size_mb: Max file size in MB before rotation
            retention_days: Days to keep rotated logs
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        self.logger.handlers = []  # Clear existing handlers

        # Create log directory if it doesn't exist
        if log_to_file:
            log_path = Path(log_dir)
            log_path.mkdir(exist_ok=True)

        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(JSONFormatter())
            self.logger.addHandler(console_handler)

        # File handler with rotation
        if log_to_file:
            log_file_path = Path(log_dir) / log_file
            file_handler = logging.handlers.RotatingFileHandler(
                log_file_path,
                maxBytes=rotation_size_mb * 1024 * 1024,
                backupCount=retention_days,
            )
            file_handler.setFormatter(JSONFormatter())
            self.logger.addHandler(file_handler)

        # Separate error log file
        if log_to_file:
            error_log_path = Path(log_dir) / "errors.log"
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_path,
                maxBytes=rotation_size_mb * 1024 * 1024,
                backupCount=retention_days,
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(JSONFormatter())
            self.logger.addHandler(error_handler)

    def log_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        query_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Log user query"""
        extra = {
            "event_type": "user_query",
            "event_data": {
                "query": query,
                "query_length": len(query),
                **kwargs,
            },
        }
        if session_id:
            extra["session_id"] = session_id
        if query_id:
            extra["query_id"] = query_id

        self.logger.info("User query received", extra=extra)

    def log_query_processing_start(
        self,
        query: str,
        session_id: Optional[str] = None,
        query_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Log query processing start"""
        extra = {
            "event_type": "query_processing_start",
            "event_data": {
                "query": query,
                **kwargs,
            },
        }
        if session_id:
            extra["session_id"] = session_id
        if query_id:
            extra["query_id"] = query_id

        self.logger.info("Query processing started", extra=extra)

    def log_response(
        self,
        query: str,
        response: str,
        response_time: float,
        tool_used: Optional[str] = None,
        session_id: Optional[str] = None,
        query_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Log server response"""
        extra = {
            "event_type": "response_generated",
            "event_data": {
                "query": query,
                "response": response,
                "response_length": len(response),
                "response_time": round(response_time, 3),
                "tool_used": tool_used,
                **kwargs,
            },
        }
        if session_id:
            extra["session_id"] = session_id
        if query_id:
            extra["query_id"] = query_id

        self.logger.info("Response generated", extra=extra)

    def log_response_displayed(
        self,
        response: str,
        session_id: Optional[str] = None,
        query_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Log when response is displayed to user"""
        extra = {
            "event_type": "response_displayed",
            "event_data": {
                "response_length": len(response),
                **kwargs,
            },
        }
        if session_id:
            extra["session_id"] = session_id
        if query_id:
            extra["query_id"] = query_id

        self.logger.info("Response displayed", extra=extra)

    def log_tool_execution_start(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        session_id: Optional[str] = None,
        query_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Log tool execution start"""
        # Sanitize tool args (remove sensitive data if needed)
        sanitized_args = self._sanitize_args(tool_args)

        extra = {
            "event_type": "tool_execution_start",
            "event_data": {
                "tool_name": tool_name,
                "tool_args": sanitized_args,
                **kwargs,
            },
        }
        if session_id:
            extra["session_id"] = session_id
        if query_id:
            extra["query_id"] = query_id

        self.logger.info(f"Tool execution started: {tool_name}", extra=extra)

    def log_tool_execution_end(
        self,
        tool_name: str,
        execution_time: float,
        success: bool = True,
        result_summary: Optional[str] = None,
        session_id: Optional[str] = None,
        query_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Log tool execution end"""
        extra = {
            "event_type": "tool_execution_end",
            "event_data": {
                "tool_name": tool_name,
                "execution_time": round(execution_time, 3),
                "success": success,
                "result_summary": result_summary,
                **kwargs,
            },
        }
        if session_id:
            extra["session_id"] = session_id
        if query_id:
            extra["query_id"] = query_id

        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, f"Tool execution completed: {tool_name}", extra=extra)

    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        query_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Log error with full context"""
        extra = {
            "event_type": "error",
            "event_data": {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {},
                **kwargs,
            },
        }
        if session_id:
            extra["session_id"] = session_id
        if query_id:
            extra["query_id"] = query_id

        self.logger.error(
            f"Error occurred: {type(error).__name__}: {str(error)}",
            extra=extra,
            exc_info=True,
        )

    def log_metric(
        self,
        metric_name: str,
        value: float,
        unit: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Log performance metric"""
        extra = {
            "event_type": "performance_metric",
            "event_data": {
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
                **kwargs,
            },
        }
        if session_id:
            extra["session_id"] = session_id

        self.logger.info(f"Metric: {metric_name}={value}", extra=extra)

    def log_warning(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Log warning message"""
        extra = {
            "event_type": "warning",
            "event_data": {
                "message": message,
                "context": context or {},
                **kwargs,
            },
        }
        if session_id:
            extra["session_id"] = session_id

        self.logger.warning(message, extra=extra)

    def _sanitize_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize tool arguments (remove sensitive data if needed)"""
        # For now, just return as-is
        # In the future, can add PII redaction, etc.
        return args


# Global logger instance
_logger_instance: Optional[StructuredLogger] = None


def get_logger(
    log_dir: Optional[str] = None,
    log_file: Optional[str] = None,
    log_level: Optional[str] = None,
) -> StructuredLogger:
    """
    Get or create global logger instance

    Args:
        log_dir: Directory for log files (default: from env or "logs")
        log_file: Main log file name (default: from env or "app.log")
        log_level: Logging level (default: from env or "INFO")

    Returns:
        StructuredLogger instance
    """
    global _logger_instance

    if _logger_instance is None:
        # Load configuration from environment variables
        log_dir = log_dir or os.getenv("LOG_DIR", "logs")
        log_file = log_file or os.getenv("LOG_FILE", "app.log")
        log_level = log_level or os.getenv("LOG_LEVEL", "INFO")
        log_to_console = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
        log_to_file = os.getenv("LOG_TO_FILE", "true").lower() == "true"
        rotation_size_mb = int(os.getenv("LOG_ROTATION_SIZE", "10"))
        retention_days = int(os.getenv("LOG_RETENTION_DAYS", "30"))

        _logger_instance = StructuredLogger(
            name="money_minder",
            log_dir=log_dir,
            log_file=log_file,
            log_level=log_level,
            log_to_console=log_to_console,
            log_to_file=log_to_file,
            rotation_size_mb=rotation_size_mb,
            retention_days=retention_days,
        )

    return _logger_instance
