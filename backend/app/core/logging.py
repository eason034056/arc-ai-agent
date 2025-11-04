"""
Logging Module

This module configures structured logging for the entire application.
It supports both JSON and text formats for different environments.

Key Features:
- Structured logging with context
- JSON format for production (machine-readable)
- Text format for development (human-readable)
- Integration with FastAPI request logging
- Proper log levels and filtering

Usage:
    from app.core.logging import get_logger
    
    logger = get_logger(__name__)
    logger.info("Processing payroll", extra={"batch_id": "123", "month": "2025-11"})
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any

from app.core.config import get_settings


class JSONFormatter(logging.Formatter):
    """
    Custom JSON Formatter for Structured Logging
    
    This formatter converts log records to JSON format,
    making them easy to parse and analyze in log aggregation systems.
    
    Each log entry includes:
    - timestamp: ISO 8601 format timestamp
    - level: Log level (INFO, WARNING, ERROR, etc.)
    - logger: Name of the logger (usually module name)
    - message: Log message
    - extra: Any additional context data
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as JSON
        
        Args:
            record: LogRecord instance from Python's logging module
            
        Returns:
            JSON string representation of the log record
        """
        # Create base log entry with standard fields
        log_entry: dict[str, Any] = {
            # ISO 8601 timestamp for international compatibility
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            
            # Log level (INFO, WARNING, ERROR, etc.)
            "level": record.levelname,
            
            # Logger name (usually module path like "app.agent.nodes.compute")
            "logger": record.name,
            
            # The actual log message
            "message": record.getMessage(),
        }
        
        # Add exception information if present
        # This happens when logger.exception() is called
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add any extra fields passed via logger.info("msg", extra={...})
        # These fields appear at the root level of the JSON object
        if hasattr(record, "extra"):
            log_entry.update(record.extra)
        
        # Convert to JSON string
        # ensure_ascii=False: Allow Unicode characters
        return json.dumps(log_entry, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """
    Human-Readable Text Formatter
    
    This formatter creates traditional text log entries
    that are easy to read during development.
    
    Format: [TIMESTAMP] LEVEL - LOGGER - MESSAGE
    Example: [2025-11-04 10:30:45] INFO - app.agent.graph - Starting payroll batch
    """
    
    def __init__(self):
        """
        Initialize the text formatter with a specific format string
        
        Format string components:
        - %(asctime)s: Timestamp
        - %(levelname)-8s: Log level (left-aligned, 8 characters)
        - %(name)s: Logger name
        - %(message)s: Log message
        """
        super().__init__(
            fmt="[%(asctime)s] %(levelname)-8s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logging() -> None:
    """
    Configure application-wide logging
    
    This function:
    1. Gets logging configuration from settings
    2. Creates a console handler (stdout)
    3. Attaches the appropriate formatter (JSON or text)
    4. Sets the log level
    5. Configures the root logger
    
    Call this once at application startup (in main.py)
    """
    # Get application settings
    settings = get_settings()
    
    # Create console handler that writes to stdout
    # stdout is better than stderr for Docker logs
    handler = logging.StreamHandler(sys.stdout)
    
    # Choose formatter based on configuration
    # JSON for production (machine-readable)
    # Text for development (human-readable)
    if settings.log_format == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())
    
    # Configure the root logger
    # All loggers inherit from the root logger
    root_logger = logging.getLogger()
    
    # Remove any existing handlers
    # This prevents duplicate log entries
    root_logger.handlers.clear()
    
    # Add our configured handler
    root_logger.addHandler(handler)
    
    # Set log level from configuration
    # DEBUG < INFO < WARNING < ERROR < CRITICAL
    root_logger.setLevel(settings.log_level)
    
    # Optionally quiet noisy third-party libraries
    # Uncomment these if you want less verbose output
    # logging.getLogger("uvicorn").setLevel(logging.WARNING)
    # logging.getLogger("web3").setLevel(logging.WARNING)
    # logging.getLogger("slack_bolt").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module
    
    Args:
        name: Logger name (usually __name__ of the calling module)
        
    Returns:
        Logger instance configured with application settings
        
    Usage:
        # At the top of your module
        from app.core.logging import get_logger
        
        logger = get_logger(__name__)
        
        # Later in your code
        logger.info("Processing started")
        logger.error("Something went wrong", extra={"user_id": "123"})
        
    Example with context:
        logger.info(
            "Payroll batch created",
            extra={
                "batch_id": batch.id,
                "month": batch.month,
                "line_count": len(batch.lines)
            }
        )
    """
    return logging.getLogger(name)

