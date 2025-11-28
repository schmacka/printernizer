"""
Custom middleware for Printernizer.
German compliance, security headers, and request timing middleware.
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger()


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Middleware to track request timing and log performance metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and measure timing."""
        start_time = time.time()

        try:
            # Process the request
            response = await call_next(request)

            # Calculate timing
            process_time = time.time() - start_time

            # Add timing header
            response.headers["X-Process-Time"] = str(process_time)

            # Log request details
            logger.info(
                "Request processed",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=process_time,
                user_agent=request.headers.get("user-agent", "")
            )

            return response
        except Exception:
            # Re-raise the exception to be handled by exception handlers
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers for GDPR compliance and security."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        try:
            response = await call_next(request)

            # Security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

            # Content Security Policy
            # Allow images from local network (printer cameras)
            # Using http://*:* to allow HTTP images from any host (primarily for printer cameras)
            # Allow cdn.jsdelivr.net for Swagger UI/ReDoc documentation
            # Allow fonts.googleapis.com and fonts.gstatic.com for ReDoc fonts
            # Allow fastapi.tiangolo.com for documentation favicons
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "img-src 'self' data: blob: http://*:* https://cdn.jsdelivr.net https://fastapi.tiangolo.com; "
                "connect-src 'self' ws: wss:; "
                "font-src 'self' https://fonts.gstatic.com"
            )
            response.headers["Content-Security-Policy"] = csp

            # GDPR and privacy headers
            response.headers["Permissions-Policy"] = (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            )

            return response
        except Exception:
            # Re-raise the exception to be handled by exception handlers
            raise


class GermanComplianceMiddleware(BaseHTTPMiddleware):
    """Middleware for German GDPR compliance and data protection."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Ensure German compliance standards."""
        try:
            # Log data processing for GDPR audit trail
            if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
                logger.info(
                    "Data processing request",
                    method=request.method,
                    path=request.url.path,
                    ip_hash=hash(request.client.host if request.client else "unknown"),
                    timestamp=time.time(),
                    gdpr_audit=True
                )

            response = await call_next(request)

            # Add German compliance headers
            response.headers["X-GDPR-Compliant"] = "true"
            response.headers["X-Data-Location"] = "Germany"
            response.headers["X-Privacy-Policy"] = "/privacy"

            # Ensure proper timezone handling
            response.headers["X-Timezone"] = "Europe/Berlin"

            return response
        except Exception:
            # Re-raise the exception to be handled by exception handlers
            raise