"""
Custom middleware for Printernizer.
German compliance, security headers, and request timing middleware.
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

# Prometheus collectors (reused via default registry)
try:
    from prometheus_client import Counter, Histogram
    try:
        REQUEST_COUNT = Counter('printernizer_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
        REQUEST_DURATION = Histogram('printernizer_request_duration_seconds', 'Request duration')
    except ValueError:
        # Already registered, fetch from registry
        from prometheus_client import REGISTRY
        REQUEST_COUNT = REGISTRY._names_to_collectors['printernizer_requests_total']
        REQUEST_DURATION = REGISTRY._names_to_collectors['printernizer_request_duration_seconds']
except Exception:  # pragma: no cover - metrics optional in some environments
    REQUEST_COUNT = None
    REQUEST_DURATION = None

logger = structlog.get_logger()


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Middleware to track request timing and log performance metrics."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and measure timing."""
        start_time = time.time()
        
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
        # Prometheus metrics
        try:
            if REQUEST_COUNT is not None and REQUEST_DURATION is not None:
                route = request.scope.get("route")
                endpoint = getattr(route, "path", None) or request.url.path
                REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status=str(response.status_code)).inc()
                REQUEST_DURATION.observe(process_time)
        except Exception:
            # Avoid breaking requests if metrics encounter an issue
            pass
        
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers for GDPR compliance and security."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' ws: wss:; "
            "font-src 'self'"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # GDPR and privacy headers
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
        
        return response


class GermanComplianceMiddleware(BaseHTTPMiddleware):
    """Middleware for German GDPR compliance and data protection."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Ensure German compliance standards."""
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