"""
Standardized error handling for Printernizer API.

This module provides consistent error response formats and exception classes
for all API endpoints. All errors follow a standardized JSON format with
proper HTTP status codes and structured error details.

Error Response Format:
    {
        "status": "error",
        "message": "User-friendly error message",
        "error_code": "PRINTER_NOT_FOUND",
        "details": {
            "printer_id": "abc123",
            "additional": "context"
        },
        "timestamp": "2025-11-08T15:30:00Z"
    }

Success Response Format:
    {
        "status": "success",
        "data": { ... },
        "message": "Optional success message"
    }

Usage:
    from src.utils.errors import PrinterNotFoundError, success_response

    # Raise domain-specific error
    if not printer:
        raise PrinterNotFoundError(printer_id)

    # Return success response
    return success_response(printer)

See Also:
    - docs/ERROR_HANDLING_AUDIT.md - Error handling patterns
    - Phase 3 documentation for standardization approach
"""

from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()


# =============================================================================
# Base Exception Class
# =============================================================================

class PrinternizerError(Exception):
    """
    Base exception for all Printernizer errors.

    All custom exceptions inherit from this class to enable global
    exception handling and consistent error responses.

    Attributes:
        message: User-friendly error message
        status_code: HTTP status code for the error
        error_code: Machine-readable error code for frontend handling
        details: Additional context as dictionary

    Example:
        >>> error = PrinternizerError(
        ...     message="Resource not found",
        ...     status_code=404,
        ...     error_code="RESOURCE_NOT_FOUND",
        ...     details={"resource_id": "123"}
        ... )
    """

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize PrinternizerError.

        Args:
            message: User-friendly error message
            status_code: HTTP status code (default: 500)
            error_code: Machine-readable error code (default: derived from class name)
            details: Additional error context
        """
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self._generate_error_code()
        self.details = details or {}
        super().__init__(message)

    def _generate_error_code(self) -> str:
        """
        Generate error code from class name.

        Converts class name from CamelCase to UPPER_SNAKE_CASE.
        Example: PrinterNotFoundError -> PRINTER_NOT_FOUND

        Returns:
            Error code string
        """
        import re
        # Remove 'Error' suffix if present
        name = self.__class__.__name__
        if name.endswith('Error'):
            name = name[:-5]
        # Convert CamelCase to UPPER_SNAKE_CASE
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).upper()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error to dictionary format.

        Returns:
            Dictionary with error information
        """
        return {
            "status": "error",
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "timestamp": datetime.now().isoformat()
        }


# =============================================================================
# Printer Errors
# =============================================================================

class PrinterNotFoundError(PrinternizerError):
    """Printer not found in system."""

    def __init__(self, printer_id: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize PrinterNotFoundError.

        Args:
            printer_id: ID of the printer that wasn't found
            details: Additional context
        """
        error_details = {"printer_id": printer_id}
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Printer not found: {printer_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            details=error_details
        )


class PrinterConnectionError(PrinternizerError):
    """Failed to connect to printer."""

    def __init__(self, printer_id: str, reason: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize PrinterConnectionError.

        Args:
            printer_id: ID of the printer
            reason: Connection failure reason
            details: Additional context
        """
        error_details = {"printer_id": printer_id, "reason": reason}
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Failed to connect to printer: {reason}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=error_details
        )


class PrinterBusyError(PrinternizerError):
    """Printer is busy and cannot accept command."""

    def __init__(self, printer_id: str, current_status: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize PrinterBusyError.

        Args:
            printer_id: ID of the printer
            current_status: Current printer status
            details: Additional context
        """
        error_details = {"printer_id": printer_id, "current_status": current_status}
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Printer is busy (status: {current_status})",
            status_code=status.HTTP_409_CONFLICT,
            details=error_details
        )


class PrinterAlreadyExistsError(PrinternizerError):
    """Printer with this identifier already exists."""

    def __init__(self, identifier: str, identifier_type: str = "ip_address", details: Optional[Dict[str, Any]] = None):
        """
        Initialize PrinterAlreadyExistsError.

        Args:
            identifier: The duplicate identifier value
            identifier_type: Type of identifier (ip_address, serial_number, etc.)
            details: Additional context
        """
        error_details = {identifier_type: identifier}
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Printer with this {identifier_type} already exists: {identifier}",
            status_code=status.HTTP_409_CONFLICT,
            details=error_details
        )


class PrinterDisconnectedError(PrinternizerError):
    """Printer is disconnected and cannot process command."""

    def __init__(self, printer_id: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize PrinterDisconnectedError.

        Args:
            printer_id: ID of the disconnected printer
            details: Additional context
        """
        error_details = {"printer_id": printer_id}
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Printer is disconnected: {printer_id}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=error_details
        )


# =============================================================================
# Job Errors
# =============================================================================

class JobNotFoundError(PrinternizerError):
    """Job not found in system."""

    def __init__(self, job_id: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize JobNotFoundError.

        Args:
            job_id: ID of the job that wasn't found
            details: Additional context
        """
        error_details = {"job_id": job_id}
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Job not found: {job_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            details=error_details
        )


class JobAlreadyStartedError(PrinternizerError):
    """Job has already started and cannot be modified."""

    def __init__(self, job_id: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize JobAlreadyStartedError.

        Args:
            job_id: ID of the job
            details: Additional context
        """
        error_details = {"job_id": job_id}
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Job has already started and cannot be modified: {job_id}",
            status_code=status.HTTP_409_CONFLICT,
            details=error_details
        )


class JobInvalidStatusError(PrinternizerError):
    """Job cannot be updated to invalid status."""

    def __init__(self, job_id: str, current_status: str, requested_status: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize JobInvalidStatusError.

        Args:
            job_id: ID of the job
            current_status: Current job status
            requested_status: Requested invalid status
            details: Additional context
        """
        error_details = {
            "job_id": job_id,
            "current_status": current_status,
            "requested_status": requested_status
        }
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Invalid status transition from {current_status} to {requested_status}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=error_details
        )


# =============================================================================
# File Errors
# =============================================================================

class FileNotFoundError(PrinternizerError):
    """File not found in system."""

    def __init__(self, file_id: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize FileNotFoundError.

        Args:
            file_id: ID of the file that wasn't found
            details: Additional context
        """
        error_details = {"file_id": file_id}
        if details:
            error_details.update(details)

        super().__init__(
            message=f"File not found: {file_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            details=error_details
        )


class FileDownloadError(PrinternizerError):
    """Failed to download file from printer."""

    def __init__(self, filename: str, printer_id: str, reason: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize FileDownloadError.

        Args:
            filename: Name of the file
            printer_id: ID of the printer
            reason: Download failure reason
            details: Additional context
        """
        error_details = {
            "filename": filename,
            "printer_id": printer_id,
            "reason": reason
        }
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Failed to download file '{filename}': {reason}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=error_details
        )


class InvalidFileTypeError(PrinternizerError):
    """File type is not supported."""

    def __init__(self, filename: str, file_type: str, supported_types: list, details: Optional[Dict[str, Any]] = None):
        """
        Initialize InvalidFileTypeError.

        Args:
            filename: Name of the file
            file_type: Unsupported file type
            supported_types: List of supported file types
            details: Additional context
        """
        error_details = {
            "filename": filename,
            "file_type": file_type,
            "supported_types": supported_types
        }
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Unsupported file type '{file_type}'. Supported: {', '.join(supported_types)}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=error_details
        )


class FileProcessingError(PrinternizerError):
    """Failed to process file (thumbnails, metadata, etc.)."""

    def __init__(self, file_id: str, operation: str, reason: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize FileProcessingError.

        Args:
            file_id: ID of the file
            operation: Processing operation that failed
            reason: Failure reason
            details: Additional context
        """
        error_details = {
            "file_id": file_id,
            "operation": operation,
            "reason": reason
        }
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Failed to {operation} file: {reason}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=error_details
        )


# =============================================================================
# Material Errors
# =============================================================================

class MaterialNotFoundError(PrinternizerError):
    """Material not found in system."""

    def __init__(self, material_id: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize MaterialNotFoundError.

        Args:
            material_id: ID of the material that wasn't found
            details: Additional context
        """
        error_details = {"material_id": material_id}
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Material not found: {material_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            details=error_details
        )


class InsufficientMaterialError(PrinternizerError):
    """Insufficient material available for operation."""

    def __init__(self, material_id: str, required: float, available: float, details: Optional[Dict[str, Any]] = None):
        """
        Initialize InsufficientMaterialError.

        Args:
            material_id: ID of the material
            required: Required amount
            available: Available amount
            details: Additional context
        """
        error_details = {
            "material_id": material_id,
            "required": required,
            "available": available
        }
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Insufficient material: required {required}g, available {available}g",
            status_code=status.HTTP_409_CONFLICT,
            details=error_details
        )


# =============================================================================
# Library Errors
# =============================================================================

class LibraryItemNotFoundError(PrinternizerError):
    """Library item not found."""

    def __init__(self, item_id: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize LibraryItemNotFoundError.

        Args:
            item_id: ID of the library item
            details: Additional context
        """
        error_details = {"item_id": item_id}
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Library item not found: {item_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            details=error_details
        )


# =============================================================================
# General Errors
# =============================================================================

class ValidationError(PrinternizerError):
    """Input validation failed."""

    def __init__(self, field: str, error: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize ValidationError.

        Args:
            field: Field that failed validation
            error: Validation error message
            details: Additional context
        """
        error_details = {"field": field, "error": error}
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Validation failed for '{field}': {error}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=error_details
        )


class ServiceUnavailableError(PrinternizerError):
    """Service or feature is temporarily unavailable."""

    def __init__(self, service: str, reason: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize ServiceUnavailableError.

        Args:
            service: Service name
            reason: Unavailability reason
            details: Additional context
        """
        error_details = {"service": service, "reason": reason}
        if details:
            error_details.update(details)

        super().__init__(
            message=f"{service} is unavailable: {reason}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=error_details
        )


class ConfigurationError(PrinternizerError):
    """Configuration is invalid or missing."""

    def __init__(self, config_key: str, issue: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize ConfigurationError.

        Args:
            config_key: Configuration key with issue
            issue: Description of the issue
            details: Additional context
        """
        error_details = {"config_key": config_key, "issue": issue}
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Configuration error for '{config_key}': {issue}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=error_details
        )


class DatabaseError(PrinternizerError):
    """Database operation failed."""

    def __init__(self, operation: str, reason: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize DatabaseError.

        Args:
            operation: Database operation that failed (query, insert, update, etc.)
            reason: Failure reason
            details: Additional context
        """
        error_details = {"operation": operation, "reason": reason}
        if details:
            error_details.update(details)

        super().__init__(
            message=f"Database {operation} failed: {reason}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=error_details
        )


class FileOperationError(PrinternizerError):
    """File operation failed."""

    def __init__(self, operation: str, filename: str, reason: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize FileOperationError.

        Args:
            operation: File operation that failed (read, write, delete, etc.)
            filename: Name of the file
            reason: Failure reason
            details: Additional context
        """
        error_details = {
            "operation": operation,
            "filename": filename,
            "reason": reason
        }
        if details:
            error_details.update(details)

        super().__init__(
            message=f"File {operation} failed for '{filename}': {reason}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=error_details
        )


class AuthenticationError(PrinternizerError):
    """Authentication failed."""

    def __init__(self, reason: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        """
        Initialize AuthenticationError.

        Args:
            reason: Authentication failure reason
            details: Additional context
        """
        error_details = {"reason": reason}
        if details:
            error_details.update(details)

        super().__init__(
            message=reason,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=error_details
        )


class AuthorizationError(PrinternizerError):
    """Authorization failed (insufficient permissions)."""

    def __init__(self, reason: str = "Insufficient permissions", resource: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        Initialize AuthorizationError.

        Args:
            reason: Authorization failure reason
            resource: Resource that access was denied to
            details: Additional context
        """
        error_details = {"reason": reason}
        if resource:
            error_details["resource"] = resource
        if details:
            error_details.update(details)

        super().__init__(
            message=reason,
            status_code=status.HTTP_403_FORBIDDEN,
            details=error_details
        )


class ResourceConflictError(PrinternizerError):
    """Resource conflict (duplicate, locked, etc.)."""

    def __init__(self, resource_type: str, resource_id: str, reason: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize ResourceConflictError.

        Args:
            resource_type: Type of resource (printer, job, file, etc.)
            resource_id: ID of the conflicting resource
            reason: Conflict reason
            details: Additional context
        """
        error_details = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "reason": reason
        }
        if details:
            error_details.update(details)

        super().__init__(
            message=f"{resource_type.capitalize()} conflict: {reason}",
            status_code=status.HTTP_409_CONFLICT,
            details=error_details
        )


class NotFoundError(PrinternizerError):
    """Generic resource not found error."""

    def __init__(self, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize NotFoundError.

        Args:
            resource_type: Type of resource (snapshot, camera, etc.)
            resource_id: ID of the resource not found
            details: Additional context
        """
        error_details = {
            "resource_type": resource_type,
            "resource_id": resource_id
        }
        if details:
            error_details.update(details)

        super().__init__(
            message=f"{resource_type.capitalize()} not found: {resource_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            details=error_details
        )


# =============================================================================
# Response Helper Functions
# =============================================================================

def error_response(
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create a standardized error response.

    Use this for errors that don't have a specific exception class.

    Args:
        message: User-friendly error message
        status_code: HTTP status code
        error_code: Machine-readable error code
        details: Additional error details

    Returns:
        JSONResponse with standardized error format

    Example:
        >>> return error_response(
        ...     message="Resource locked",
        ...     status_code=409,
        ...     error_code="RESOURCE_LOCKED",
        ...     details={"resource_id": "123"}
        ... )
    """
    content = {
        "status": "error",
        "message": message,
        "error_code": error_code or "UNKNOWN_ERROR",
        "details": details or {},
        "timestamp": datetime.now().isoformat()
    }

    logger.error(
        "API error response",
        status_code=status_code,
        error_code=error_code,
        message=message,
        details=details
    )

    return JSONResponse(status_code=status_code, content=content)


def success_response(
    data: Any,
    status_code: int = status.HTTP_200_OK,
    message: Optional[str] = None
) -> JSONResponse:
    """
    Create a standardized success response.

    Args:
        data: Response data (dict, list, or Pydantic model)
        status_code: HTTP status code (default: 200)
        message: Optional success message

    Returns:
        JSONResponse with standardized success format

    Example:
        >>> return success_response(
        ...     data={"printer_id": "123", "status": "connected"},
        ...     message="Printer connected successfully"
        ... )
    """
    # Handle Pydantic models
    if hasattr(data, 'model_dump'):
        data = data.model_dump()
    elif hasattr(data, 'dict'):
        data = data.dict()

    content = {
        "status": "success",
        "data": data
    }

    if message:
        content["message"] = message

    return JSONResponse(status_code=status_code, content=content)


# =============================================================================
# Global Exception Handlers
# =============================================================================

async def printernizer_exception_handler(request: Request, exc: PrinternizerError) -> JSONResponse:
    """
    Global exception handler for PrinternizerError and subclasses.

    Automatically converts custom exceptions to standardized JSON responses.

    Args:
        request: FastAPI request object
        exc: PrinternizerError instance

    Returns:
        JSONResponse with error details
    """
    logger.error(
        "Printernizer error",
        error_code=exc.error_code,
        status_code=exc.status_code,
        message=exc.message,
        details=exc.details,
        path=request.url.path,
        method=request.method
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unexpected errors.

    Catches all unhandled exceptions and returns standardized error response
    without exposing internal details.

    Args:
        request: FastAPI request object
        exc: Exception instance

    Returns:
        JSONResponse with generic error message
    """
    logger.error(
        "Unhandled exception",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True
    )

    # Don't expose internal error details in production
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An unexpected error occurred. Please try again later.",
            "error_code": "INTERNAL_SERVER_ERROR",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handler for FastAPI HTTPException to convert to standard format.

    Converts FastAPI's default HTTPException format to our standardized format.

    Args:
        request: FastAPI request object
        exc: HTTPException instance

    Returns:
        JSONResponse with standardized error format
    """
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "error_code": f"HTTP_{exc.status_code}",
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
    )
