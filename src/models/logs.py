"""
Pydantic models for the unified log viewer system.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """Log severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"


class LogSource(str, Enum):
    """Log source types."""
    FRONTEND = "frontend"
    BACKEND = "backend"
    ERRORS = "errors"


class NormalizedLogEntry(BaseModel):
    """Normalized log entry from any source."""
    id: str = Field(..., description="Unique log entry identifier")
    source: LogSource = Field(..., description="Source of the log entry")
    timestamp: datetime = Field(..., description="When the log was created")
    level: LogLevel = Field(..., description="Log severity level")
    category: str = Field(..., description="Log category (e.g., PRINTER, API, download)")
    message: str = Field(..., description="Log message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional details")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Context information")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LogQueryFilters(BaseModel):
    """Filters for querying logs."""
    source: Optional[LogSource] = Field(default=None, description="Filter by log source")
    level: Optional[LogLevel] = Field(default=None, description="Filter by minimum level")
    category: Optional[str] = Field(default=None, description="Filter by category")
    search: Optional[str] = Field(default=None, description="Full-text search in message")
    start_date: Optional[datetime] = Field(default=None, description="Start of date range")
    end_date: Optional[datetime] = Field(default=None, description="End of date range")
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=50, ge=1, le=200, description="Items per page")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order by timestamp")


class LogPagination(BaseModel):
    """Pagination information for log queries."""
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")


class LogStatistics(BaseModel):
    """Aggregated statistics across log sources."""
    total: int = Field(..., description="Total number of logs")
    last_24h: int = Field(..., description="Logs in the last 24 hours")
    by_level: Dict[str, int] = Field(..., description="Count by log level")
    by_source: Dict[str, int] = Field(..., description="Count by source")
    by_category: Dict[str, int] = Field(..., description="Count by category")


class LogSourceInfo(BaseModel):
    """Information about a log source."""
    source: LogSource = Field(..., description="Source identifier")
    name: str = Field(..., description="Display name")
    count: int = Field(..., description="Number of logs from this source")
    available: bool = Field(..., description="Whether this source is available")


class LogQueryResult(BaseModel):
    """Result of a log query."""
    data: List[NormalizedLogEntry] = Field(..., description="Log entries")
    pagination: LogPagination = Field(..., description="Pagination info")
    statistics: Optional[LogStatistics] = Field(default=None, description="Optional statistics")


class LogSourcesResponse(BaseModel):
    """Response for log sources endpoint."""
    sources: List[LogSourceInfo] = Field(..., description="Available log sources")


class LogExportFormat(str, Enum):
    """Export format options."""
    JSON = "json"
    CSV = "csv"
