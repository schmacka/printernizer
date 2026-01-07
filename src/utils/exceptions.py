"""
Custom exceptions for Printernizer.

DEPRECATED: This module is deprecated. Use src/utils/errors.py instead.

The classes in this module are maintained for backward compatibility only.
All new code should import from src.utils.errors instead.

Migration Guide:
    # Old (deprecated)
    from src.utils.exceptions import PrinterConnectionError, NotFoundError

    # New (preferred)
    from src.utils.errors import PrinterConnectionError, NotFoundError

Note: The legacy classes have slightly different signatures than the new ones.
The legacy classes are kept as wrappers that maintain backward compatibility
with existing code that uses the old signatures.

TODO: Remove this module once all code has been migrated to use errors.py
"""
import warnings
from datetime import datetime
from typing import Optional, Dict, Any

# Import new error classes for re-export
from src.utils.errors import (
    PrinternizerError,
    PrinterConnectionError as NewPrinterConnectionError,
    NotFoundError as NewNotFoundError,
    ConfigurationError as NewConfigurationError,
    DatabaseError as NewDatabaseError,
    FileOperationError as NewFileOperationError,
    ValidationError as NewValidationError,
    AuthenticationError as NewAuthenticationError,
    AuthorizationError as NewAuthorizationError,
)


class PrinternizerException(Exception):
    """
    Base exception class for Printernizer application.

    DEPRECATED: Use PrinternizerError from src.utils.errors instead.

    This class is maintained for backward compatibility. New code should use
    PrinternizerError which provides:
    - Automatic error_code generation from class name
    - to_dict() method for JSON serialization
    - Better structured error details
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize exception with structured error information."""
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error to dictionary format.

        Added for compatibility with PrinternizerError interface.
        """
        return {
            "status": "error",
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class ConfigurationError(PrinternizerException):
    """
    Exception raised for configuration-related errors.

    DEPRECATED: Use ConfigurationError from src.utils.errors instead.

    Legacy signature: ConfigurationError(message, details=None)
    New signature: ConfigurationError(config_key, issue, details=None)
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details=details
        )


class DatabaseError(PrinternizerException):
    """
    Exception raised for database-related errors.

    DEPRECATED: Use DatabaseError from src.utils.errors instead.

    Legacy signature: DatabaseError(message, details=None)
    New signature: DatabaseError(operation, reason, details=None)
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details=details
        )


class PrinterConnectionError(PrinternizerException):
    """
    Exception raised when printer connection fails.

    DEPRECATED: Use PrinterConnectionError from src.utils.errors instead.

    Legacy signature: PrinterConnectionError(printer_id, message, details=None)
    New signature: PrinterConnectionError(printer_id, reason, details=None)

    Note: The new version uses 'reason' instead of 'message' as the second parameter.
    """

    def __init__(self, printer_id: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Printer connection failed for {printer_id}: {message}",
            error_code="PRINTER_CONNECTION_ERROR",
            status_code=503,
            details={"printer_id": printer_id, **(details or {})}
        )


class FileOperationError(PrinternizerException):
    """
    Exception raised for file operation errors.

    DEPRECATED: Use FileOperationError from src.utils.errors instead.

    Legacy signature: FileOperationError(operation, filename, message, details=None)
    New signature: FileOperationError(operation, filename, reason, details=None)

    Note: The new version uses 'reason' instead of 'message' as the third parameter.
    """

    def __init__(self, operation: str, filename: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"File {operation} failed for {filename}: {message}",
            error_code="FILE_OPERATION_ERROR",
            status_code=500,
            details={"operation": operation, "filename": filename, **(details or {})}
        )


class ValidationError(PrinternizerException):
    """
    Exception raised for validation errors.

    DEPRECATED: Use ValidationError from src.utils.errors instead.

    Legacy signature: ValidationError(field, message, details=None)
    New signature: ValidationError(field, error, details=None)

    Note: The new version uses 'error' instead of 'message' as the second parameter.
    """

    def __init__(self, field: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Validation failed for {field}: {message}",
            error_code="VALIDATION_ERROR",
            status_code=422,
            details={"field": field, **(details or {})}
        )


class AuthenticationError(PrinternizerException):
    """
    Exception raised for authentication errors.

    DEPRECATED: Use AuthenticationError from src.utils.errors instead.

    Legacy signature: AuthenticationError(message="Authentication failed", details=None)
    New signature: AuthenticationError(reason="Authentication failed", details=None)

    Note: The new version uses 'reason' instead of 'message'.
    """

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details
        )


class AuthorizationError(PrinternizerException):
    """
    Exception raised for authorization errors.

    DEPRECATED: Use AuthorizationError from src.utils.errors instead.

    Legacy signature: AuthorizationError(message="Insufficient permissions", details=None)
    New signature: AuthorizationError(reason="Insufficient permissions", resource=None, details=None)

    Note: The new version uses 'reason' instead of 'message' and adds optional 'resource'.
    """

    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
            details=details
        )


class NotFoundError(PrinternizerException):
    """
    Exception raised when a resource is not found.

    DEPRECATED: Use NotFoundError from src.utils.errors instead.

    Both legacy and new versions have the same signature:
    NotFoundError(resource_type, resource_id, details=None)
    """

    def __init__(self, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"{resource_type} '{resource_id}' not found",
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id, **(details or {})}
        )


# =============================================================================
# Migration Aliases
# =============================================================================
# These aliases point to the new error classes from errors.py for cases where
# code has already been migrated. Import from src.utils.errors directly instead.

# Re-export new classes for convenience during migration
# (allows gradual migration without breaking existing imports)
__all__ = [
    # Legacy classes (deprecated)
    "PrinternizerException",
    "ConfigurationError",
    "DatabaseError",
    "PrinterConnectionError",
    "FileOperationError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    # New base class (for migration)
    "PrinternizerError",
]
