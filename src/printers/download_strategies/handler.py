"""
Download handler that coordinates multiple download strategies.

Manages strategy selection, retries, and fallbacks for robust file downloads.
"""

import asyncio
from typing import List, Optional
import structlog

from src.config.constants import RetrySettings
from .base import (
    DownloadStrategy,
    DownloadResult,
    DownloadOptions,
    DownloadError,
    FatalDownloadError,
    RetryableDownloadError
)

logger = structlog.get_logger()


class DownloadHandler:
    """Orchestrates file downloads using multiple strategies with retry logic.

    The handler tries strategies in order, retrying each strategy multiple times
    before falling back to the next one. This provides robust downloads with
    automatic fallback to alternative protocols.
    """

    def __init__(self, printer_id: str, strategies: List[DownloadStrategy]):
        """Initialize download handler.

        Args:
            printer_id: Unique identifier for the printer
            strategies: List of download strategies to try (in priority order)
        """
        self.printer_id = printer_id
        self.strategies = strategies
        self.logger = logger.bind(printer_id=printer_id)

    async def download(
        self,
        filename: str,
        local_path: str,
        max_retries_per_strategy: int = RetrySettings.MAX_DOWNLOAD_RETRIES
    ) -> DownloadResult:
        """Download a file using available strategies with retry logic.

        Args:
            filename: Name of file to download
            local_path: Local path to save the file
            max_retries_per_strategy: Max retry attempts per strategy

        Returns:
            DownloadResult with success status and details
        """
        options = DownloadOptions(
            filename=filename,
            local_path=local_path,
            max_retries=max_retries_per_strategy
        )

        total_attempts = 0
        all_errors = []

        # Try each strategy in order
        for strategy in self.strategies:
            # Check if strategy is available
            try:
                is_available = await strategy.is_available()
                if not is_available:
                    self.logger.debug(
                        "Strategy not available, skipping",
                        strategy=strategy.name
                    )
                    continue
            except Exception as e:
                self.logger.debug(
                    "Error checking strategy availability",
                    strategy=strategy.name,
                    error=str(e)
                )
                continue

            self.logger.info(
                "Attempting download with strategy",
                filename=filename,
                strategy=strategy.name
            )

            # Try this strategy with retries
            for attempt in range(max_retries_per_strategy):
                total_attempts += 1

                try:
                    result = await strategy.download(options)

                    if result.success:
                        self.logger.info(
                            "Download successful",
                            filename=filename,
                            strategy=strategy.name,
                            size=result.size_bytes,
                            attempts=total_attempts
                        )
                        result.attempts = total_attempts
                        result.strategy_used = strategy.name
                        return result

                    # Strategy returned failure (not exception)
                    error_msg = result.error or "Unknown error"
                    all_errors.append(f"{strategy.name}: {error_msg}")
                    self.logger.debug(
                        "Strategy attempt failed",
                        strategy=strategy.name,
                        attempt=attempt + 1,
                        error=error_msg
                    )

                except FatalDownloadError as e:
                    # Fatal error, don't retry this strategy
                    all_errors.append(f"{strategy.name}: {str(e)} (fatal)")
                    self.logger.warning(
                        "Fatal error with strategy, moving to next",
                        strategy=strategy.name,
                        error=str(e)
                    )
                    break  # Move to next strategy

                except RetryableDownloadError as e:
                    # Retryable error, try again after delay
                    all_errors.append(f"{strategy.name}: {str(e)} (retry {attempt + 1})")
                    self.logger.debug(
                        "Retryable error, will retry",
                        strategy=strategy.name,
                        attempt=attempt + 1,
                        max_retries=max_retries_per_strategy,
                        error=str(e)
                    )

                    if attempt < max_retries_per_strategy - 1:
                        # Exponential backoff
                        delay = RetrySettings.DOWNLOAD_RETRY_DELAY * (2 ** attempt)
                        await asyncio.sleep(delay)

                except Exception as e:
                    # Unexpected error, treat as retryable
                    all_errors.append(f"{strategy.name}: {str(e)} (unexpected)")
                    self.logger.error(
                        "Unexpected error during download",
                        strategy=strategy.name,
                        attempt=attempt + 1,
                        error=str(e),
                        error_type=type(e).__name__
                    )

                    if attempt < max_retries_per_strategy - 1:
                        delay = RetrySettings.DOWNLOAD_RETRY_DELAY * (2 ** attempt)
                        await asyncio.sleep(delay)

        # All strategies failed
        error_summary = "; ".join(all_errors)
        self.logger.error(
            "All download strategies failed",
            filename=filename,
            total_attempts=total_attempts,
            strategies_tried=len(self.strategies),
            errors=error_summary
        )

        return DownloadResult(
            success=False,
            file_path=local_path,
            error=f"All strategies failed: {error_summary}",
            attempts=total_attempts
        )

    async def get_available_strategies(self) -> List[str]:
        """Get list of currently available strategy names.

        Returns:
            List of strategy names that are available
        """
        available = []
        for strategy in self.strategies:
            try:
                if await strategy.is_available():
                    available.append(strategy.name)
            except Exception:
                pass
        return available

    def add_strategy(self, strategy: DownloadStrategy, priority: int = -1) -> None:
        """Add a new strategy to the handler.

        Args:
            strategy: Strategy to add
            priority: Position to insert (-1 for end)
        """
        if priority < 0:
            self.strategies.append(strategy)
        else:
            self.strategies.insert(priority, strategy)

    def remove_strategy(self, strategy_name: str) -> bool:
        """Remove a strategy by name.

        Args:
            strategy_name: Name of strategy to remove

        Returns:
            True if strategy was removed, False if not found
        """
        for i, strategy in enumerate(self.strategies):
            if strategy.name == strategy_name:
                self.strategies.pop(i)
                return True
        return False
