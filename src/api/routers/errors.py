"""Error reporting and monitoring endpoints."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import structlog
from pathlib import Path

from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field

logger = structlog.get_logger()
router = APIRouter()


class ErrorReport(BaseModel):
    """Frontend error report model."""
    id: str
    timestamp: str
    category: str
    message: str
    stack: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    userAgent: str
    url: str
    severity: str
    userMessage: Optional[str] = None


class SessionInfo(BaseModel):
    """Session information for error reports."""
    sessionId: str
    timestamp: str
    userAgent: str
    url: str
    viewport: Dict[str, int] = Field(default_factory=dict)


class ErrorReportRequest(BaseModel):
    """Error report request model."""
    errors: List[ErrorReport]
    session: SessionInfo


class ErrorStoreService:
    """Service for storing and managing error reports."""
    
    def __init__(self):
        self.error_log_path = Path("data/logs/frontend_errors.jsonl")
        self.max_errors_per_session = 50
        self.ensure_log_directory()
    
    def ensure_log_directory(self):
        """Ensure the log directory exists."""
        self.error_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def store_errors(self, errors: List[ErrorReport], session: SessionInfo) -> bool:
        """Store error reports to file."""
        try:
            # Prepare log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "session": session.dict(),
                "errors": [error.dict() for error in errors],
                "count": len(errors)
            }
            
            # Append to log file
            with open(self.error_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            # Log to structured logger
            logger.info(
                "Frontend errors reported",
                session_id=session.sessionId,
                error_count=len(errors),
                categories=[error.category for error in errors],
                severities=[error.severity for error in errors]
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to store frontend errors", error=str(e))
            return False
    
    def get_recent_errors(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent error reports."""
        try:
            if not self.error_log_path.exists():
                return []
            
            errors = []
            with open(self.error_log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Get last N lines
            for line in lines[-limit:]:
                try:
                    error_entry = json.loads(line.strip())
                    errors.append(error_entry)
                except json.JSONDecodeError:
                    continue
            
            return list(reversed(errors))  # Most recent first
            
        except Exception as e:
            logger.error("Failed to retrieve frontend errors", error=str(e))
            return []
    
    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for the specified time period."""
        try:
            cutoff_time = datetime.now().timestamp() - (hours * 3600)
            recent_errors = self.get_recent_errors(1000)  # Get more for analysis
            
            # Filter by time
            filtered_errors = []
            for entry in recent_errors:
                entry_time = datetime.fromisoformat(entry['timestamp']).timestamp()
                if entry_time >= cutoff_time:
                    filtered_errors.extend(entry['errors'])
            
            # Calculate statistics
            total_errors = len(filtered_errors)
            categories = {}
            severities = {}
            sessions = set()
            
            for error in filtered_errors:
                # Count by category
                category = error.get('category', 'unknown')
                categories[category] = categories.get(category, 0) + 1
                
                # Count by severity
                severity = error.get('severity', 'unknown')
                severities[severity] = severities.get(severity, 0) + 1
            
            # Count unique sessions from recent entries
            for entry in recent_errors:
                if datetime.fromisoformat(entry['timestamp']).timestamp() >= cutoff_time:
                    sessions.add(entry['session']['sessionId'])
            
            return {
                "period_hours": hours,
                "total_errors": total_errors,
                "unique_sessions": len(sessions),
                "categories": categories,
                "severities": severities,
                "error_rate": total_errors / max(len(sessions), 1)  # Errors per session
            }
            
        except Exception as e:
            logger.error("Failed to calculate error statistics", error=str(e))
            return {
                "period_hours": hours,
                "total_errors": 0,
                "unique_sessions": 0,
                "categories": {},
                "severities": {},
                "error_rate": 0
            }


# Global error store instance
error_store = ErrorStoreService()


@router.post("/report")
async def report_errors(
    request: ErrorReportRequest,
    client_request: Request
):
    """Receive and store frontend error reports."""
    try:
        # Add client IP to session info if available
        client_ip = client_request.client.host if client_request.client else "unknown"
        
        # Store errors
        success = error_store.store_errors(request.errors, request.session)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store error reports"
            )
        
        # Log high-severity errors immediately
        critical_errors = [e for e in request.errors if e.severity in ['critical', 'high']]
        if critical_errors:
            logger.warning(
                "Critical frontend errors detected",
                session_id=request.session.sessionId,
                client_ip=client_ip,
                critical_error_count=len(critical_errors),
                critical_errors=[{
                    "category": e.category,
                    "message": e.message,
                    "context": e.context
                } for e in critical_errors]
            )
        
        return {
            "status": "success",
            "message": f"Stored {len(request.errors)} error reports",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error reporting endpoint failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/recent")
async def get_recent_errors(limit: int = 50):
    """Get recent error reports for monitoring."""
    try:
        errors = error_store.get_recent_errors(limit)
        return {
            "errors": errors,
            "count": len(errors),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("Failed to get recent errors", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve error reports"
        )


@router.get("/statistics")
async def get_error_statistics(hours: int = 24):
    """Get error statistics for monitoring dashboard."""
    try:
        stats = error_store.get_error_statistics(hours)
        return {
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("Failed to get error statistics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate error statistics"
        )


@router.get("/health")
async def error_system_health():
    """Check error reporting system health."""
    try:
        # Check if log file is writable
        test_file = error_store.error_log_path.parent / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        
        # Get basic statistics
        recent_stats = error_store.get_error_statistics(1)  # Last hour
        
        return {
            "status": "healthy",
            "log_path": str(error_store.error_log_path),
            "recent_errors": recent_stats["total_errors"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Error system health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }