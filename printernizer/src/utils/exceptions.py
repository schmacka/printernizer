"""
Custom exceptions for Printernizer.
Provides structured error handling with proper HTTP status codes.
"""
from datetime import datetime
from typing import Optional, Dict, Any


class PrinternizerException(Exception):
    """Base exception class for Printernizer application."""
    
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


class ConfigurationError(PrinternizerException):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details=details
        )


class DatabaseError(PrinternizerException):
    """Exception raised for database-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR", 
            status_code=500,
            details=details
        )


class PrinterConnectionError(PrinternizerException):
    """Exception raised when printer connection fails."""
    
    def __init__(self, printer_id: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Printer connection failed for {printer_id}: {message}",
            error_code="PRINTER_CONNECTION_ERROR",
            status_code=503,
            details={"printer_id": printer_id, **(details or {})}
        )


class FileOperationError(PrinternizerException):
    """Exception raised for file operation errors."""
    
    def __init__(self, operation: str, filename: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"File {operation} failed for {filename}: {message}",
            error_code="FILE_OPERATION_ERROR",
            status_code=500,
            details={"operation": operation, "filename": filename, **(details or {})}
        )


class ValidationError(PrinternizerException):
    """Exception raised for validation errors."""
    
    def __init__(self, field: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Validation failed for {field}: {message}",
            error_code="VALIDATION_ERROR",
            status_code=422,
            details={"field": field, **(details or {})}
        )


class AuthenticationError(PrinternizerException):
    """Exception raised for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details
        )


class AuthorizationError(PrinternizerException):
    """Exception raised for authorization errors."""
    
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
            details=details
        )


class NotFoundError(PrinternizerException):
    """Exception raised when a resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"{resource_type} '{resource_id}' not found",
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id, **(details or {})}
        )