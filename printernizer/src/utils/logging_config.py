"""
Logging configuration for Printernizer.
Structured logging setup with German timezone support.
"""
import logging
import os
import sys
from typing import Any
import structlog
from pathlib import Path


def setup_logging(log_level: str = None, log_file: str = None):
    """Set up structured logging for Printernizer.

    Args:
        log_level: Log level (debug, info, warning, error). If None, reads from LOG_LEVEL env var.
        log_file: Optional path to log file.
    """

    # Read from environment variable if not provided
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO)
    )
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add file logging if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
    
    # Use JSON formatter in production, human-readable in development
    if log_level.upper() == "DEBUG":
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def mask_sensitive_data(data: Any, sensitive_fields: set = None) -> Any:
    """
    Mask sensitive data in dictionaries before logging.

    Args:
        data: Data to mask (dict, list, or other type)
        sensitive_fields: Set of field names to mask. If None, uses default set.

    Returns:
        Copy of data with sensitive fields masked

    Example:
        >>> config = {'name': 'Printer1', 'api_key': 'secret123', 'access_code': 'abc'}
        >>> mask_sensitive_data(config)
        {'name': 'Printer1', 'api_key': '***MASKED***', 'access_code': '***MASKED***'}
    """
    if sensitive_fields is None:
        sensitive_fields = {'api_key', 'access_code', 'password', 'token', 'secret', 'credential'}

    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            # Check if this field should be masked
            if key.lower() in sensitive_fields or any(s in key.lower() for s in sensitive_fields):
                masked[key] = '***MASKED***'
            else:
                # Recursively mask nested structures
                masked[key] = mask_sensitive_data(value, sensitive_fields)
        return masked
    elif isinstance(data, (list, tuple)):
        return type(data)(mask_sensitive_data(item, sensitive_fields) for item in data)
    else:
        return data