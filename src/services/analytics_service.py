"""
Analytics service for business reporting and statistics.
This will be expanded in Phase 4 with complete business analytics.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import structlog
from database.database import Database

logger = structlog.get_logger()


class AnalyticsService:
    """Service for business analytics and reporting."""
    
    def __init__(self, database: Database):
        """Initialize analytics service."""
        self.database = database
        
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get main dashboard statistics."""
        # TODO: Implement actual analytics calculations
        return {
            "total_jobs": 0,
            "active_printers": 0,
            "total_runtime": 0,
            "material_used": 0.0,
            "estimated_costs": 0.0,
            "business_jobs": 0,
            "private_jobs": 0
        }
        
    async def get_printer_usage(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get printer usage statistics."""
        # TODO: Implement printer usage analytics
        return []
        
    async def get_material_consumption(self, days: int = 30) -> Dict[str, Any]:
        """Get material consumption statistics."""
        # TODO: Implement material tracking
        return {
            "total_consumption": 0.0,
            "by_material": {},
            "cost_breakdown": {}
        }
        
    async def get_business_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate business report for given period."""
        try:
            logger.info("Generating business report", 
                       start=start_date.isoformat(), end=end_date.isoformat())
            
            # Get jobs within the period
            jobs = await self.database.get_jobs_by_date_range(
                start_date.isoformat(), end_date.isoformat()
            )
            
            # Separate business and private jobs
            business_jobs = [j for j in jobs if j.get('is_business', False)]
            private_jobs = [j for j in jobs if not j.get('is_business', False)]
            
            # Calculate revenue and costs
            total_revenue = sum(j.get('cost_eur', 0.0) for j in business_jobs)
            material_costs = sum(j.get('material_used_grams', 0.0) * 0.025 for j in jobs)  # Estimate €0.025/gram
            power_costs = sum(j.get('elapsed_time_minutes', 0) * 0.002 for j in jobs)  # Estimate €0.002/minute
            profit = total_revenue - material_costs - power_costs
            
            # Calculate total material consumption
            total_material = sum(j.get('material_used_grams', 0.0) for j in jobs)
            
            return {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "jobs": {
                    "total": len(jobs),
                    "business": len(business_jobs),
                    "private": len(private_jobs)
                },
                "revenue": {
                    "total": total_revenue,
                    "material_costs": material_costs,
                    "power_costs": power_costs,
                    "profit": profit
                },
                "materials": {
                    "consumed": total_material,
                    "costs": material_costs
                }
            }
        except Exception as e:
            logger.error("Error generating business report", error=str(e))
            return {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "jobs": {
                    "total": 0,
                    "business": 0,
                    "private": 0
                },
                "revenue": {
                    "total": 0.0,
                    "material_costs": 0.0,
                    "power_costs": 0.0,
                    "profit": 0.0
                },
                "materials": {
                    "consumed": 0.0,
                    "costs": 0.0
                }
            }
        
    async def export_data(self, format_type: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Export data in specified format (CSV, Excel)."""
        # TODO: Implement data export functionality
        logger.info("Exporting data (placeholder)", format=format_type, filters=filters)
        
        return {
            "status": "success",
            "message": "Data export not yet implemented",
            "format": format_type,
            "file_path": None
        }
        
    async def get_summary(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get analytics summary for the specified period."""
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Get jobs within the period
            jobs = await self.database.get_jobs_by_date_range(
                start_date.isoformat(), end_date.isoformat()
            )
            
            # Calculate statistics
            total_jobs = len(jobs)
            completed_jobs = len([j for j in jobs if j.get('status') == 'completed'])
            failed_jobs = len([j for j in jobs if j.get('status') == 'failed'])
            
            total_print_time_hours = sum(j.get('elapsed_time_minutes', 0) for j in jobs) / 60.0
            total_material_used_kg = sum(j.get('material_used_grams', 0.0) for j in jobs) / 1000.0
            total_cost_eur = sum(j.get('cost_eur', 0.0) for j in jobs)
            
            average_job_duration_hours = total_print_time_hours / total_jobs if total_jobs > 0 else 0.0
            success_rate_percent = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0.0
            
            return {
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "total_print_time_hours": round(total_print_time_hours, 2),
                "total_material_used_kg": round(total_material_used_kg, 3),
                "total_cost_eur": round(total_cost_eur, 2),
                "average_job_duration_hours": round(average_job_duration_hours, 2),
                "success_rate_percent": round(success_rate_percent, 1)
            }
        except Exception as e:
            logger.error("Error getting analytics summary", error=str(e))
            raise e
            
    async def get_business_analytics(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get business analytics for the specified period."""
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Get jobs within the period
            jobs = await self.database.get_jobs_by_date_range(
                start_date.isoformat(), end_date.isoformat()
            )
            
            # Separate business and private jobs
            business_jobs = [j for j in jobs if j.get('is_business', False)]
            private_jobs = [j for j in jobs if not j.get('is_business', False)]
            
            # Calculate business revenue and costs
            business_revenue = sum(j.get('cost_eur', 0.0) for j in business_jobs)
            business_material_cost = sum(j.get('material_used_grams', 0.0) * 0.025 for j in business_jobs)
            business_profit = business_revenue - business_material_cost
            
            # Calculate top customers
            customer_stats = {}
            for job in business_jobs:
                customer = job.get('customer_name', 'Unknown')
                if customer not in customer_stats:
                    customer_stats[customer] = {
                        'name': customer,
                        'job_count': 0,
                        'total_revenue': 0.0
                    }
                customer_stats[customer]['job_count'] += 1
                customer_stats[customer]['total_revenue'] += job.get('cost_eur', 0.0)
            
            # Sort customers by revenue
            top_customers = sorted(
                customer_stats.values(),
                key=lambda x: x['total_revenue'],
                reverse=True
            )[:5]  # Top 5 customers
            
            return {
                "business_jobs": len(business_jobs),
                "private_jobs": len(private_jobs),
                "business_revenue_eur": round(business_revenue, 2),
                "business_material_cost_eur": round(business_material_cost, 2),
                "business_profit_eur": round(business_profit, 2),
                "top_customers": top_customers
            }
        except Exception as e:
            logger.error("Error getting business analytics", error=str(e))
            raise e
        
    async def get_dashboard_overview(self, period: str = 'day') -> Dict[str, Any]:
        """Get dashboard overview statistics for the specified period."""
        try:
            # Get job statistics
            jobs_data = await self._get_job_statistics(period)
            
            # Get file statistics
            files_data = await self._get_file_statistics()
            
            # Get printer statistics
            printers_data = await self._get_printer_statistics()
            
            return {
                "jobs": jobs_data,
                "files": files_data,
                "printers": printers_data
            }
            
        except Exception as e:
            logger.error("Error getting dashboard overview", error=str(e))
            # Return default structure to prevent frontend errors
            return {
                "jobs": {
                    "total_jobs": 0,
                    "completed_jobs": 0,
                    "success_rate": 0.0
                },
                "files": {
                    "total_files": 0,
                    "downloaded_files": 0
                },
                "printers": {
                    "total_printers": 0,
                    "online_printers": 0
                }
            }
    
    async def _get_job_statistics(self, period: str) -> Dict[str, Any]:
        """Get job statistics for the specified period."""
        try:
            # Query jobs from database based on period
            # TODO: Implement actual database queries based on period
            total_jobs = 0
            completed_jobs = 0
            success_rate = 0.0
            
            return {
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "success_rate": success_rate
            }
        except Exception as e:
            logger.error("Error getting job statistics", error=str(e))
            return {
                "total_jobs": 0,
                "completed_jobs": 0,
                "success_rate": 0.0
            }
    
    async def _get_file_statistics(self) -> Dict[str, Any]:
        """Get file statistics."""
        try:
            # Get file statistics from database
            file_stats = await self.database.get_file_statistics()
            
            return {
                "total_files": file_stats.get("total_files", 0),
                "downloaded_files": file_stats.get("downloaded_files", 0)
            }
        except Exception as e:
            logger.error("Error getting file statistics", error=str(e))
            return {
                "total_files": 0,
                "downloaded_files": 0
            }
    
    async def _get_printer_statistics(self) -> Dict[str, Any]:
        """Get printer statistics.""" 
        try:
            # Query printers from database
            printers = await self.database.list_printers()
            
            total_printers = len(printers)
            online_printers = len([p for p in printers if p.get('status') == 'online'])
            
            return {
                "total_printers": total_printers,
                "online_printers": online_printers
            }
        except Exception as e:
            logger.error("Error getting printer statistics", error=str(e))
            return {
                "total_printers": 0,
                "online_printers": 0
            }