"""
Custom middleware for Printernizer.
German compliance, security headers, rate limiting, and request timing middleware.
"""
import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Callable, Dict, List, Optional, Set
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import structlog

logger = structlog.get_logger()


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting rules."""
    requests_per_minute: int = 100
    burst_size: int = 20  # Allow short bursts above the rate limit
    cleanup_interval: int = 300  # Clean up old entries every 5 minutes


@dataclass
class RateLimitEntry:
    """Tracks rate limit state for a single client."""
    tokens: float = 100.0  # Current token count (token bucket algorithm)
    last_update: float = field(default_factory=time.time)
    request_count: int = 0  # Total requests in current window


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to protect against brute force and DoS attacks.

    Uses a token bucket algorithm for smooth rate limiting:
    - Each client has a bucket of tokens
    - Tokens are consumed on each request
    - Tokens regenerate over time at a fixed rate
    - Allows short bursts while enforcing long-term rate limits

    Protected endpoints (stricter limits):
    - POST /api/v1/printers (create printer)
    - POST /api/v1/setup/* (setup endpoints)
    - POST /api/v1/settings (settings changes)
    - DELETE endpoints (destructive operations)
    """

    # Endpoints with stricter rate limits (requests per minute)
    PROTECTED_ENDPOINTS: Dict[str, int] = {
        "POST /api/v1/printers": 10,
        "POST /api/v1/setup": 20,
        "POST /api/v1/settings": 30,
        "DELETE": 20,  # All DELETE operations
    }

    # Endpoints exempt from rate limiting
    EXEMPT_ENDPOINTS: Set[str] = {
        "/api/v1/health",
        "/api/v1/ws",
        "/metrics",
    }

    def __init__(
        self,
        app,
        config: Optional[RateLimitConfig] = None
    ):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self._buckets: Dict[str, RateLimitEntry] = defaultdict(
            lambda: RateLimitEntry(tokens=float(self.config.requests_per_minute))
        )
        self._lock = Lock()
        self._last_cleanup = time.time()

    def _get_client_key(self, request: Request) -> str:
        """Get a unique key for the client (IP address)."""
        # Get client IP, considering potential proxy headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain (original client)
            client_ip = forwarded_for.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host
        else:
            client_ip = "unknown"
        return client_ip

    def _get_rate_limit(self, request: Request) -> int:
        """Determine the rate limit for this request."""
        method = request.method
        path = request.url.path

        # Check for protected endpoints
        endpoint_key = f"{method} {path}"

        for pattern, limit in self.PROTECTED_ENDPOINTS.items():
            if pattern == method:  # Method-only pattern (e.g., "DELETE")
                return limit
            if endpoint_key.startswith(pattern):
                return limit

        return self.config.requests_per_minute

    def _is_exempt(self, request: Request) -> bool:
        """Check if this request is exempt from rate limiting."""
        path = request.url.path
        for exempt in self.EXEMPT_ENDPOINTS:
            if path.startswith(exempt):
                return True
        return False

    def _cleanup_old_entries(self):
        """Remove old entries to prevent memory growth."""
        current_time = time.time()
        if current_time - self._last_cleanup < self.config.cleanup_interval:
            return

        with self._lock:
            # Remove entries that haven't been used in the last hour
            stale_threshold = current_time - 3600
            stale_keys = [
                key for key, entry in self._buckets.items()
                if entry.last_update < stale_threshold
            ]
            for key in stale_keys:
                del self._buckets[key]

            self._last_cleanup = current_time

            if stale_keys:
                logger.debug(
                    "Rate limit cleanup",
                    removed_entries=len(stale_keys),
                    remaining_entries=len(self._buckets)
                )

    def _check_rate_limit(self, client_key: str, rate_limit: int) -> tuple[bool, float]:
        """
        Check if the request is allowed using token bucket algorithm.

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        current_time = time.time()

        with self._lock:
            entry = self._buckets[client_key]

            # Calculate tokens to add since last request
            # Tokens regenerate at rate_limit per minute
            time_passed = current_time - entry.last_update
            tokens_to_add = (time_passed / 60.0) * rate_limit

            # Update token count (cap at burst_size above rate_limit)
            max_tokens = rate_limit + self.config.burst_size
            entry.tokens = min(max_tokens, entry.tokens + tokens_to_add)
            entry.last_update = current_time

            # Check if we have tokens available
            if entry.tokens >= 1.0:
                entry.tokens -= 1.0
                entry.request_count += 1
                return True, 0.0
            else:
                # Calculate retry after (time to regenerate 1 token)
                retry_after = (1.0 - entry.tokens) * 60.0 / rate_limit
                return False, retry_after

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Periodic cleanup
        self._cleanup_old_entries()

        # Check if exempt
        if self._is_exempt(request):
            return await call_next(request)

        client_key = self._get_client_key(request)
        rate_limit = self._get_rate_limit(request)

        is_allowed, retry_after = self._check_rate_limit(client_key, rate_limit)

        if not is_allowed:
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_key,
                path=request.url.path,
                method=request.method,
                rate_limit=rate_limit,
                retry_after=retry_after
            )

            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "message": "Too many requests. Please try again later.",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "details": {
                        "retry_after_seconds": round(retry_after, 1),
                        "rate_limit_per_minute": rate_limit
                    }
                },
                headers={
                    "Retry-After": str(int(retry_after) + 1),
                    "X-RateLimit-Limit": str(rate_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + retry_after))
                }
            )

        # Add rate limit headers to successful responses
        response = await call_next(request)

        with self._lock:
            entry = self._buckets[client_key]
            remaining = max(0, int(entry.tokens))

        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response


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
            # Security-hardened CSP with minimal inline permissions
            #
            # script-src:
            #   - 'self': Allow scripts from same origin
            #   - 'unsafe-eval': Required for Swagger UI/ReDoc (JSON Schema validation)
            #   - cdn.jsdelivr.net: Swagger UI assets
            #   NOTE: 'unsafe-inline' removed - all inline scripts moved to external files
            #
            # style-src:
            #   - 'unsafe-inline': Required for dynamically generated styles (component libraries)
            #   - Fonts and CDN for documentation UI
            #
            # img-src:
            #   - http://*:*: Allow printer camera images from local network (HTTP cameras)
            #   - data/blob: For dynamically generated images
            #
            # connect-src:
            #   - ws/wss: WebSocket connections for real-time updates
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-eval' https://cdn.jsdelivr.net; "
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