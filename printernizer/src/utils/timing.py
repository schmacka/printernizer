"""
Timing utilities for performance monitoring and optimization.
"""

import time
import asyncio
from contextlib import contextmanager, asynccontextmanager
from typing import Optional
import structlog

logger = structlog.get_logger()


@contextmanager
def timed_operation(operation_name: str, log_level: str = "info"):
    """
    Context manager for timing synchronous operations.

    Usage:
        with timed_operation("Database initialization"):
            database.initialize()

    Args:
        operation_name: Name of the operation being timed
        log_level: Log level for timing output (default: "info")
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start_time
        duration_ms = round(duration * 1000, 2)

        log_func = getattr(logger, log_level, logger.info)
        log_func(
            f"⏱️  {operation_name}",
            duration_ms=duration_ms,
            duration_seconds=round(duration, 2)
        )


@asynccontextmanager
async def timed_async_operation(operation_name: str, log_level: str = "info"):
    """
    Async context manager for timing asynchronous operations.

    Usage:
        async with timed_async_operation("Database initialization"):
            await database.initialize()

    Args:
        operation_name: Name of the operation being timed
        log_level: Log level for timing output (default: "info")
    """
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start_time
        duration_ms = round(duration * 1000, 2)

        log_func = getattr(logger, log_level, logger.info)
        log_func(
            f"⏱️  {operation_name}",
            duration_ms=duration_ms,
            duration_seconds=round(duration, 2)
        )


class StartupTimer:
    """
    Track startup performance metrics across multiple operations.

    Usage:
        timer = StartupTimer()
        timer.start("Database")
        # ... database initialization ...
        timer.end("Database")

        timer.report()
    """

    def __init__(self):
        """Initialize startup timer."""
        self.operations = {}
        self.start_times = {}
        self.total_start_time = time.perf_counter()

    def start(self, operation_name: str):
        """Start timing an operation."""
        self.start_times[operation_name] = time.perf_counter()

    def end(self, operation_name: str):
        """End timing an operation."""
        if operation_name not in self.start_times:
            logger.warning(f"No start time found for operation: {operation_name}")
            return

        start_time = self.start_times[operation_name]
        duration = time.perf_counter() - start_time
        self.operations[operation_name] = duration

        # Log individual operation
        logger.debug(
            f"⏱️  {operation_name}",
            duration_ms=round(duration * 1000, 2),
            duration_seconds=round(duration, 2)
        )

    def report(self):
        """Generate and log comprehensive startup performance report."""
        total_duration = time.perf_counter() - self.total_start_time

        logger.info("=" * 60)
        logger.info("📊 STARTUP PERFORMANCE REPORT")
        logger.info("=" * 60)

        # Sort operations by duration (slowest first)
        sorted_ops = sorted(
            self.operations.items(),
            key=lambda x: x[1],
            reverse=True
        )

        for operation_name, duration in sorted_ops:
            percentage = (duration / total_duration) * 100 if total_duration > 0 else 0
            logger.info(
                f"  {operation_name}",
                duration_ms=round(duration * 1000, 2),
                duration_seconds=round(duration, 2),
                percentage=round(percentage, 1)
            )

        logger.info("=" * 60)
        logger.info(
            "Total startup time",
            total_ms=round(total_duration * 1000, 2),
            total_seconds=round(total_duration, 2)
        )
        logger.info("=" * 60)

    def get_total_duration(self) -> float:
        """Get total duration since timer was created."""
        return time.perf_counter() - self.total_start_time

    def get_operation_duration(self, operation_name: str) -> Optional[float]:
        """Get duration of a specific operation."""
        return self.operations.get(operation_name)
