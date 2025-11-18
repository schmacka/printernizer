"""
Monitoring and alerting service for error tracking and system health.
"""

import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from src.config.constants import PollingIntervals
from src.utils.error_handling import error_handler, ErrorSeverity
from src.utils.config import get_settings

logger = structlog.get_logger()


class MonitoringService:
    """Service for monitoring system health and error patterns."""
    
    def __init__(self):
        self.settings = get_settings()
        self.monitoring_config = {
            "check_interval": 300,  # 5 minutes
            "error_threshold": {
                "critical_per_hour": 5,
                "high_per_hour": 20,
                "total_per_hour": 100
            },
            "health_checks": {
                "database": True,
                "printer_connections": True,
                "file_system": True,
                "websocket": True
            }
        }
        self.last_alert_times = {}
        self.alert_cooldown = 3600  # 1 hour cooldown for same alert type
        
    async def start_monitoring(self) -> None:
        """Start the monitoring service."""
        logger.info("Starting monitoring service")

        # Start monitoring tasks
        asyncio.create_task(self._error_monitoring_loop())
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._cleanup_old_logs_loop())

        logger.info("Monitoring service started")

    async def _error_monitoring_loop(self) -> None:
        """Monitor error rates and patterns."""
        while True:
            try:
                await self._check_error_rates()
                await asyncio.sleep(self.monitoring_config["check_interval"])
            except Exception as e:
                logger.error("Error monitoring loop failed", error=str(e))
                await asyncio.sleep(PollingIntervals.MONITORING_SERVICE_RETRY)  # Wait 1 minute before retry

    async def _health_check_loop(self) -> None:
        """Perform periodic health checks."""
        while True:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.monitoring_config["check_interval"])
            except Exception as e:
                logger.error("Health check loop failed", error=str(e))
                await asyncio.sleep(PollingIntervals.MONITORING_SERVICE_RETRY)  # Wait 1 minute before retry
    
    async def _cleanup_old_logs_loop(self):
        """Clean up old log files."""
        while True:
            try:
                await self._cleanup_old_logs()
                await asyncio.sleep(PollingIntervals.MONITORING_SERVICE_DAILY)  # Run daily
            except Exception as e:
                logger.error("Log cleanup loop failed", error=str(e))
                await asyncio.sleep(PollingIntervals.MONITORING_SERVICE_ERROR_BACKOFF)  # Wait 1 hour before retry
    
    async def _check_error_rates(self):
        """Check error rates and trigger alerts if necessary."""
        try:
            # Get error statistics for the last hour
            stats = error_handler.get_error_statistics(hours=1)
            thresholds = self.monitoring_config["error_threshold"]
            
            # Check critical errors
            critical_count = stats["by_severity"].get("critical", 0)
            if critical_count >= thresholds["critical_per_hour"]:
                await self._trigger_alert(
                    "critical_error_rate",
                    f"Critical error rate exceeded: {critical_count} critical errors in the last hour",
                    {"critical_errors": critical_count, "threshold": thresholds["critical_per_hour"]}
                )
            
            # Check high severity errors
            high_count = stats["by_severity"].get("high", 0)
            if high_count >= thresholds["high_per_hour"]:
                await self._trigger_alert(
                    "high_error_rate",
                    f"High error rate exceeded: {high_count} high severity errors in the last hour",
                    {"high_errors": high_count, "threshold": thresholds["high_per_hour"]}
                )
            
            # Check total error count
            if stats["total_errors"] >= thresholds["total_per_hour"]:
                await self._trigger_alert(
                    "total_error_rate",
                    f"Total error rate exceeded: {stats['total_errors']} errors in the last hour",
                    {"total_errors": stats["total_errors"], "threshold": thresholds["total_per_hour"]}
                )
            
            # Check for error patterns
            await self._check_error_patterns(stats)
            
        except Exception as e:
            logger.error("Failed to check error rates", error=str(e))
    
    async def _check_error_patterns(self, stats: Dict[str, Any]):
        """Check for concerning error patterns."""
        try:
            # Check if a single error category is dominating
            total_errors = stats["total_errors"]
            if total_errors > 10:  # Only check if we have significant errors
                for category, count in stats["by_category"].items():
                    if count / total_errors > 0.7:  # 70% of errors from one category
                        await self._trigger_alert(
                            f"error_pattern_{category}",
                            f"Error pattern detected: {category} errors represent {count}/{total_errors} ({count/total_errors*100:.1f}%) of recent errors",
                            {"category": category, "count": count, "total": total_errors}
                        )
            
            # Check for repeated error types
            for error_type, count in stats["by_type"].items():
                if count > 20:  # More than 20 of the same error type
                    await self._trigger_alert(
                        f"repeated_error_{error_type}",
                        f"Repeated error detected: {error_type} occurred {count} times in the last hour",
                        {"error_type": error_type, "count": count}
                    )
                    
        except Exception as e:
            logger.error("Failed to check error patterns", error=str(e))
    
    async def _perform_health_checks(self):
        """Perform system health checks."""
        try:
            health_status = {}
            
            # Database health check
            if self.monitoring_config["health_checks"]["database"]:
                health_status["database"] = await self._check_database_health()
            
            # File system health check
            if self.monitoring_config["health_checks"]["file_system"]:
                health_status["file_system"] = await self._check_file_system_health()
            
            # Log health status
            failed_checks = [check for check, status in health_status.items() if not status["healthy"]]
            if failed_checks:
                await self._trigger_alert(
                    "health_check_failed",
                    f"Health checks failed: {', '.join(failed_checks)}",
                    {"failed_checks": failed_checks, "health_status": health_status}
                )
            else:
                logger.debug("All health checks passed", health_status=health_status)
                
        except Exception as e:
            logger.error("Failed to perform health checks", error=str(e))
    
    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            # Import here to avoid circular imports
            from database.database import Database
            
            db = Database()
            
            # Try a simple query
            await db.execute_query("SELECT 1")
            
            # Check database file size
            db_path = Path(self.settings.database_path)
            if db_path.exists():
                db_size = db_path.stat().st_size
                return {
                    "healthy": True,
                    "size_bytes": db_size,
                    "last_check": datetime.now().isoformat()
                }
            else:
                return {
                    "healthy": False,
                    "error": "Database file not found",
                    "last_check": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    async def _check_file_system_health(self) -> Dict[str, Any]:
        """Check file system health."""
        try:
            # Check if we can write to data directory
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            test_file = data_dir / "health_check.tmp"
            test_file.write_text("health check")
            test_file.unlink()
            
            # Check disk space
            import shutil
            total, used, free = shutil.disk_usage(data_dir)
            free_percent = (free / total) * 100
            
            return {
                "healthy": free_percent > 10,  # Alert if less than 10% free
                "free_space_percent": free_percent,
                "free_bytes": free,
                "total_bytes": total,
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    async def _trigger_alert(self, alert_type: str, message: str, context: Dict[str, Any]):
        """Trigger an alert with cooldown."""
        try:
            current_time = datetime.now().timestamp()
            last_alert = self.last_alert_times.get(alert_type, 0)
            
            # Check cooldown
            if current_time - last_alert < self.alert_cooldown:
                return
            
            # Update last alert time
            self.last_alert_times[alert_type] = current_time
            
            # Log the alert
            logger.warning(
                f"ALERT: {alert_type}",
                alert_type=alert_type,
                message=message,
                context=context,
                timestamp=datetime.now().isoformat()
            )
            
            # Store alert in file
            await self._store_alert(alert_type, message, context)
            
            # Here you could add additional alerting mechanisms:
            # - Send webhook notifications
            # - Email alerts
            # - Slack/Discord notifications
            # - Push notifications
            
        except Exception as e:
            logger.error("Failed to trigger alert", error=str(e))
    
    async def _store_alert(self, alert_type: str, message: str, context: Dict[str, Any]):
        """Store alert information to file."""
        try:
            alert_file = Path("data/logs/alerts.jsonl")
            alert_file.parent.mkdir(parents=True, exist_ok=True)
            
            alert_data = {
                "timestamp": datetime.now().isoformat(),
                "alert_type": alert_type,
                "message": message,
                "context": context
            }
            
            with open(alert_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(alert_data) + '\n')
                
        except Exception as e:
            logger.error("Failed to store alert", error=str(e))
    
    async def _cleanup_old_logs(self):
        """Clean up old log files."""
        try:
            log_dir = Path("data/logs")
            if not log_dir.exists():
                return
            
            # Keep logs for 30 days
            cutoff_date = datetime.now() - timedelta(days=30)
            cutoff_timestamp = cutoff_date.timestamp()
            
            cleaned_files = 0
            for log_file in log_dir.glob("*.jsonl"):
                try:
                    if log_file.stat().st_mtime < cutoff_timestamp:
                        log_file.unlink()
                        cleaned_files += 1
                except Exception as e:
                    logger.warning(f"Failed to clean up log file {log_file}", error=str(e))
            
            if cleaned_files > 0:
                logger.info(f"Cleaned up {cleaned_files} old log files")
                
        except Exception as e:
            logger.error("Failed to cleanup old logs", error=str(e))
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        try:
            # Get recent error statistics
            error_stats = error_handler.get_error_statistics(hours=24)
            
            # Get recent alerts
            alert_file = Path("data/logs/alerts.jsonl")
            recent_alerts = []
            if alert_file.exists():
                try:
                    with open(alert_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # Get last 10 alerts
                    for line in lines[-10:]:
                        try:
                            alert_data = json.loads(line.strip())
                            recent_alerts.append(alert_data)
                        except json.JSONDecodeError:
                            continue
                except (OSError, FileNotFoundError, PermissionError) as e:
                    # Alert log not accessible - not critical for status endpoint
                    logger.debug("Could not read alert log for status",
                                error=str(e))
            
            # Perform quick health checks
            health_status = {
                "database": await self._check_database_health(),
                "file_system": await self._check_file_system_health()
            }
            
            return {
                "monitoring_active": True,
                "last_check": datetime.now().isoformat(),
                "error_statistics": error_stats,
                "recent_alerts": list(reversed(recent_alerts)),  # Most recent first
                "health_status": health_status,
                "configuration": self.monitoring_config
            }
            
        except Exception as e:
            logger.error("Failed to get monitoring status", error=str(e))
            return {
                "monitoring_active": False,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }


# Global monitoring service instance
monitoring_service = MonitoringService()