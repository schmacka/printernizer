"""
Analytics query functions for dashboard.

Provides aggregated statistics from usage data for the admin dashboard.
All data is already anonymous - no PII is stored or returned.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import func, distinct, desc, text
from sqlalchemy.orm import Session

from models import Submission


# Country code to name mapping for common codes
COUNTRY_NAMES = {
    "DE": "Germany",
    "US": "United States",
    "GB": "United Kingdom",
    "FR": "France",
    "ES": "Spain",
    "IT": "Italy",
    "JP": "Japan",
    "AU": "Australia",
    "CA": "Canada",
    "NL": "Netherlands",
    "BE": "Belgium",
    "AT": "Austria",
    "CH": "Switzerland",
    "PL": "Poland",
    "SE": "Sweden",
    "NO": "Norway",
    "DK": "Denmark",
    "FI": "Finland",
    "PT": "Portugal",
    "CZ": "Czech Republic",
    "RU": "Russia",
    "BR": "Brazil",
    "MX": "Mexico",
    "IN": "India",
    "CN": "China",
    "KR": "South Korea",
    "TW": "Taiwan",
    "SG": "Singapore",
    "NZ": "New Zealand",
    "ZA": "South Africa",
    "XX": "Unknown",
}

# Deployment mode display names
DEPLOYMENT_NAMES = {
    "homeassistant": "Home Assistant",
    "docker": "Docker",
    "standalone": "Standalone",
    "pi": "Raspberry Pi",
}


class AnalyticsService:
    """Service for computing dashboard analytics from aggregated statistics."""

    def __init__(self, db: Session):
        self.db = db

    def get_installation_stats(self, days_trend: int = 30) -> Dict[str, Any]:
        """
        Get installation metrics including active users and growth.

        Returns:
            Dict with total, active_7d, active_30d, growth stats, and trend data
        """
        now = datetime.utcnow()
        day_7_ago = now - timedelta(days=7)
        day_30_ago = now - timedelta(days=30)
        day_14_ago = now - timedelta(days=14)

        # Total unique installations (ever)
        total = self.db.query(
            func.count(distinct(Submission.installation_id))
        ).scalar() or 0

        # Active in last 7 days
        active_7d = self.db.query(
            func.count(distinct(Submission.installation_id))
        ).filter(
            Submission.submitted_at >= day_7_ago
        ).scalar() or 0

        # Active in last 30 days
        active_30d = self.db.query(
            func.count(distinct(Submission.installation_id))
        ).filter(
            Submission.submitted_at >= day_30_ago
        ).scalar() or 0

        # Previous 7 days (days 8-14 ago) for growth calculation
        prev_active = self.db.query(
            func.count(distinct(Submission.installation_id))
        ).filter(
            Submission.submitted_at >= day_14_ago,
            Submission.submitted_at < day_7_ago
        ).scalar() or 0

        # Calculate growth percentage
        growth_percent = 0.0
        if prev_active > 0:
            growth_percent = ((active_7d - prev_active) / prev_active) * 100

        # Generate trend data (daily counts for the last N days)
        trend = self._get_installation_trend(days_trend)

        return {
            "total": total,
            "active_7d": active_7d,
            "active_30d": active_30d,
            "growth_7d_percent": round(growth_percent, 1),
            "trend": trend
        }

    def _get_installation_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily installation counts for trend chart."""
        trend = []
        now = datetime.utcnow()

        for i in range(days - 1, -1, -1):
            day_start = (now - timedelta(days=i)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = day_start + timedelta(days=1)

            # Total unique installations up to this day
            total_up_to = self.db.query(
                func.count(distinct(Submission.installation_id))
            ).filter(
                Submission.submitted_at < day_end
            ).scalar() or 0

            # Active on this specific day
            active_on_day = self.db.query(
                func.count(distinct(Submission.installation_id))
            ).filter(
                Submission.submitted_at >= day_start,
                Submission.submitted_at < day_end
            ).scalar() or 0

            trend.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "total": total_up_to,
                "active": active_on_day
            })

        return trend

    def get_deployment_distribution(self) -> Dict[str, Any]:
        """
        Get deployment mode distribution (latest per installation).

        Returns:
            Dict with total, breakdown by mode, and percentages
        """
        # Get latest submission per installation using subquery
        latest_subq = self.db.query(
            Submission.installation_id,
            func.max(Submission.submitted_at).label('latest')
        ).group_by(Submission.installation_id).subquery()

        # Join to get deployment modes from latest submissions
        results = self.db.query(
            Submission.deployment_mode,
            func.count(Submission.installation_id).label('count')
        ).join(
            latest_subq,
            (Submission.installation_id == latest_subq.c.installation_id) &
            (Submission.submitted_at == latest_subq.c.latest)
        ).group_by(Submission.deployment_mode).all()

        total = sum(r.count for r in results)
        breakdown = {}
        percentages = {}

        for r in results:
            mode = r.deployment_mode or "unknown"
            breakdown[mode] = r.count
            percentages[mode] = round((r.count / total) * 100, 1) if total > 0 else 0

        return {
            "total": total,
            "breakdown": breakdown,
            "percentages": percentages,
            "display_names": DEPLOYMENT_NAMES
        }

    def get_version_distribution(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get version adoption rates (latest per installation).

        Args:
            limit: Maximum number of versions to return

        Returns:
            Dict with versions list, latest version, and adoption rate
        """
        # Get latest submission per installation
        latest_subq = self.db.query(
            Submission.installation_id,
            func.max(Submission.submitted_at).label('latest')
        ).group_by(Submission.installation_id).subquery()

        # Join to get versions from latest submissions
        results = self.db.query(
            Submission.app_version,
            func.count(Submission.installation_id).label('count')
        ).join(
            latest_subq,
            (Submission.installation_id == latest_subq.c.installation_id) &
            (Submission.submitted_at == latest_subq.c.latest)
        ).group_by(Submission.app_version).order_by(
            desc('count')
        ).limit(limit).all()

        total = sum(r.count for r in results)
        versions = []

        for r in results:
            version = r.app_version or "unknown"
            versions.append({
                "version": version,
                "count": r.count,
                "percentage": round((r.count / total) * 100, 1) if total > 0 else 0
            })

        # Determine latest version (highest semver would be better, but count is a proxy)
        latest_version = versions[0]["version"] if versions else None
        adoption_rate = versions[0]["percentage"] if versions else 0

        return {
            "versions": versions,
            "latest_version": latest_version,
            "adoption_rate_latest": adoption_rate,
            "total_versions": len(versions)
        }

    def get_geography_distribution(self, limit: int = 20) -> Dict[str, Any]:
        """
        Get geographic distribution by country code (latest per installation).

        Args:
            limit: Maximum number of countries to return

        Returns:
            Dict with countries list and total country count
        """
        # Get latest submission per installation
        latest_subq = self.db.query(
            Submission.installation_id,
            func.max(Submission.submitted_at).label('latest')
        ).group_by(Submission.installation_id).subquery()

        # Join to get country codes from latest submissions
        results = self.db.query(
            Submission.country_code,
            func.count(Submission.installation_id).label('count')
        ).join(
            latest_subq,
            (Submission.installation_id == latest_subq.c.installation_id) &
            (Submission.submitted_at == latest_subq.c.latest)
        ).group_by(Submission.country_code).order_by(
            desc('count')
        ).limit(limit).all()

        total = sum(r.count for r in results)
        countries = []

        for r in results:
            code = r.country_code or "XX"
            countries.append({
                "code": code,
                "name": COUNTRY_NAMES.get(code, code),
                "count": r.count,
                "percentage": round((r.count / total) * 100, 1) if total > 0 else 0
            })

        # Count total unique countries (excluding unknown)
        total_countries = len([c for c in countries if c["code"] != "XX"])

        return {
            "countries": countries,
            "total_countries": total_countries
        }

    def get_printer_stats(self) -> Dict[str, Any]:
        """
        Get aggregated printer statistics across all installations.

        Returns:
            Dict with total printers, average per installation, and type breakdown
        """
        # Get latest submission per installation
        latest_subq = self.db.query(
            Submission.installation_id,
            func.max(Submission.submitted_at).label('latest')
        ).group_by(Submission.installation_id).subquery()

        # Get printer counts from latest submissions
        results = self.db.query(
            func.sum(Submission.printer_count).label('total'),
            func.count(Submission.installation_id).label('installations'),
            func.avg(Submission.printer_count).label('average')
        ).join(
            latest_subq,
            (Submission.installation_id == latest_subq.c.installation_id) &
            (Submission.submitted_at == latest_subq.c.latest)
        ).first()

        total_printers = results.total or 0
        installations = results.installations or 0
        average = round(results.average or 0, 1)

        # Get printer type breakdown (aggregate printer_type_counts JSON)
        # This is more complex as it requires aggregating JSON fields
        type_results = self.db.query(
            Submission.printer_type_counts
        ).join(
            latest_subq,
            (Submission.installation_id == latest_subq.c.installation_id) &
            (Submission.submitted_at == latest_subq.c.latest)
        ).all()

        # Aggregate type counts across all installations
        type_totals: Dict[str, int] = {}
        for r in type_results:
            if r.printer_type_counts:
                for ptype, count in r.printer_type_counts.items():
                    type_totals[ptype] = type_totals.get(ptype, 0) + count

        return {
            "total_printers": total_printers,
            "total_installations": installations,
            "average_per_installation": average,
            "types": type_totals
        }

    def get_overview(self) -> Dict[str, Any]:
        """
        Get combined dashboard overview with all metrics.

        Returns:
            Dict with installations, deployment_modes, versions, geography, printers
        """
        return {
            "installations": self.get_installation_stats(days_trend=30),
            "deployment_modes": self.get_deployment_distribution(),
            "versions": self.get_version_distribution(limit=10),
            "geography": self.get_geography_distribution(limit=20),
            "printers": self.get_printer_stats(),
            "last_updated": datetime.utcnow().isoformat()
        }
