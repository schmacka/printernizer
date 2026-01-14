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

    def get_feature_usage(self) -> Dict[str, Any]:
        """
        Get feature usage statistics across all installations.

        Aggregates the feature_usage JSON field to show which features
        are enabled/disabled across the user base.

        Returns:
            Dict with features list showing enabled/disabled counts
        """
        # Get latest submission per installation
        latest_subq = self.db.query(
            Submission.installation_id,
            func.max(Submission.submitted_at).label('latest')
        ).group_by(Submission.installation_id).subquery()

        # Get feature_usage from latest submissions
        results = self.db.query(
            Submission.feature_usage
        ).join(
            latest_subq,
            (Submission.installation_id == latest_subq.c.installation_id) &
            (Submission.submitted_at == latest_subq.c.latest)
        ).all()

        # Aggregate feature counts
        feature_counts: Dict[str, Dict[str, int]] = {}
        total_installations = 0

        for r in results:
            total_installations += 1
            if r.feature_usage:
                for feature, enabled in r.feature_usage.items():
                    if feature not in feature_counts:
                        feature_counts[feature] = {"enabled": 0, "disabled": 0}
                    if enabled:
                        feature_counts[feature]["enabled"] += 1
                    else:
                        feature_counts[feature]["disabled"] += 1

        # Convert to list format with percentages
        features = []
        for feature, counts in sorted(feature_counts.items()):
            total = counts["enabled"] + counts["disabled"]
            features.append({
                "feature": feature,
                "enabled": counts["enabled"],
                "disabled": counts["disabled"],
                "enabled_percent": round((counts["enabled"] / total) * 100, 1) if total > 0 else 0,
                "total_reporting": total
            })

        return {
            "features": features,
            "total_installations": total_installations
        }

    def get_version_migration(self, days: int = 30) -> Dict[str, Any]:
        """
        Get version adoption over time (migration patterns).

        Shows how version distribution changes day by day.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with daily version distribution data
        """
        now = datetime.utcnow()
        migration_data = []

        # Get all unique versions first
        all_versions = set()
        version_results = self.db.query(
            distinct(Submission.app_version)
        ).all()
        for r in version_results:
            if r[0]:
                all_versions.add(r[0])

        # For each day, get version distribution
        for i in range(days - 1, -1, -1):
            day_end = (now - timedelta(days=i)).replace(
                hour=23, minute=59, second=59, microsecond=999999
            )

            # Get latest submission per installation up to this day
            latest_subq = self.db.query(
                Submission.installation_id,
                func.max(Submission.submitted_at).label('latest')
            ).filter(
                Submission.submitted_at <= day_end
            ).group_by(Submission.installation_id).subquery()

            # Count versions
            results = self.db.query(
                Submission.app_version,
                func.count(Submission.installation_id).label('count')
            ).join(
                latest_subq,
                (Submission.installation_id == latest_subq.c.installation_id) &
                (Submission.submitted_at == latest_subq.c.latest)
            ).group_by(Submission.app_version).all()

            day_data = {
                "date": day_end.strftime("%Y-%m-%d"),
                "versions": {}
            }
            for r in results:
                version = r.app_version or "unknown"
                day_data["versions"][version] = r.count

            migration_data.append(day_data)

        return {
            "migration": migration_data,
            "all_versions": sorted(list(all_versions), reverse=True)[:10]  # Top 10 versions
        }

    def get_feature_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Get feature adoption trends over time.

        Shows how feature usage changes day by day.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with daily feature adoption data
        """
        now = datetime.utcnow()
        trend_data = []

        # Get all unique features first
        all_features = set()
        feature_results = self.db.query(Submission.feature_usage).all()
        for r in feature_results:
            if r.feature_usage:
                all_features.update(r.feature_usage.keys())

        # For each day, get feature adoption
        for i in range(days - 1, -1, -1):
            day_end = (now - timedelta(days=i)).replace(
                hour=23, minute=59, second=59, microsecond=999999
            )

            # Get latest submission per installation up to this day
            latest_subq = self.db.query(
                Submission.installation_id,
                func.max(Submission.submitted_at).label('latest')
            ).filter(
                Submission.submitted_at <= day_end
            ).group_by(Submission.installation_id).subquery()

            # Get feature_usage from latest submissions
            results = self.db.query(
                Submission.feature_usage
            ).join(
                latest_subq,
                (Submission.installation_id == latest_subq.c.installation_id) &
                (Submission.submitted_at == latest_subq.c.latest)
            ).all()

            # Count enabled features
            feature_counts = {f: 0 for f in all_features}
            total = 0
            for r in results:
                total += 1
                if r.feature_usage:
                    for feature, enabled in r.feature_usage.items():
                        if enabled and feature in feature_counts:
                            feature_counts[feature] += 1

            day_data = {
                "date": day_end.strftime("%Y-%m-%d"),
                "total_installations": total,
                "features": {
                    f: {
                        "enabled": count,
                        "percent": round((count / total) * 100, 1) if total > 0 else 0
                    }
                    for f, count in feature_counts.items()
                }
            }
            trend_data.append(day_data)

        return {
            "trends": trend_data,
            "all_features": sorted(list(all_features))
        }

    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get error statistics from event_counts in submissions.

        Analyzes error patterns across installations.

        Returns:
            Dict with error statistics and trends
        """
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)

        # Get latest submission per installation
        latest_subq = self.db.query(
            Submission.installation_id,
            func.max(Submission.submitted_at).label('latest')
        ).group_by(Submission.installation_id).subquery()

        # Get event_counts from latest submissions
        results = self.db.query(
            Submission.event_counts,
            Submission.submitted_at
        ).join(
            latest_subq,
            (Submission.installation_id == latest_subq.c.installation_id) &
            (Submission.submitted_at == latest_subq.c.latest)
        ).all()

        # Aggregate error counts
        error_totals: Dict[str, int] = {}
        total_errors = 0
        installations_with_errors = 0

        for r in results:
            if r.event_counts:
                has_errors = False
                for event_type, count in r.event_counts.items():
                    if 'error' in event_type.lower() or 'fail' in event_type.lower():
                        error_totals[event_type] = error_totals.get(event_type, 0) + count
                        total_errors += count
                        has_errors = True
                if has_errors:
                    installations_with_errors += 1

        # Calculate error rates for this week vs last week
        this_week_errors = 0
        last_week_errors = 0

        week_results = self.db.query(
            Submission.event_counts,
            Submission.submitted_at
        ).filter(
            Submission.submitted_at >= two_weeks_ago
        ).all()

        for r in week_results:
            if r.event_counts:
                for event_type, count in r.event_counts.items():
                    if 'error' in event_type.lower() or 'fail' in event_type.lower():
                        if r.submitted_at >= week_ago:
                            this_week_errors += count
                        else:
                            last_week_errors += count

        # Calculate change
        error_change_percent = 0.0
        if last_week_errors > 0:
            error_change_percent = ((this_week_errors - last_week_errors) / last_week_errors) * 100

        return {
            "total_errors": total_errors,
            "installations_with_errors": installations_with_errors,
            "error_types": error_totals,
            "this_week_errors": this_week_errors,
            "last_week_errors": last_week_errors,
            "error_change_percent": round(error_change_percent, 1),
            "has_spike": error_change_percent > 50  # Flag if errors increased by >50%
        }

    def get_anomalies(self) -> Dict[str, Any]:
        """
        Detect anomalies in usage patterns.

        Checks for:
        - Sudden drops in active users
        - Error rate spikes
        - Unusual submission patterns

        Returns:
            Dict with detected anomalies and their severity
        """
        now = datetime.utcnow()
        anomalies = []

        # Check 1: Compare active users this week vs last week
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)

        active_this_week = self.db.query(
            func.count(distinct(Submission.installation_id))
        ).filter(
            Submission.submitted_at >= week_ago
        ).scalar() or 0

        active_last_week = self.db.query(
            func.count(distinct(Submission.installation_id))
        ).filter(
            Submission.submitted_at >= two_weeks_ago,
            Submission.submitted_at < week_ago
        ).scalar() or 0

        if active_last_week > 0:
            change_percent = ((active_this_week - active_last_week) / active_last_week) * 100

            if change_percent < -20:
                anomalies.append({
                    "type": "active_users_drop",
                    "severity": "high" if change_percent < -50 else "medium",
                    "message": f"Active users dropped {abs(change_percent):.1f}% compared to last week",
                    "current": active_this_week,
                    "previous": active_last_week,
                    "change_percent": round(change_percent, 1)
                })
            elif change_percent > 50:
                anomalies.append({
                    "type": "active_users_spike",
                    "severity": "info",
                    "message": f"Active users increased {change_percent:.1f}% compared to last week",
                    "current": active_this_week,
                    "previous": active_last_week,
                    "change_percent": round(change_percent, 1)
                })

        # Check 2: Submissions today vs average
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        submissions_today = self.db.query(
            func.count(Submission.id)
        ).filter(
            Submission.submitted_at >= today_start
        ).scalar() or 0

        # Average submissions per day over last 30 days
        month_ago = now - timedelta(days=30)
        total_submissions_month = self.db.query(
            func.count(Submission.id)
        ).filter(
            Submission.submitted_at >= month_ago
        ).scalar() or 0

        avg_daily = total_submissions_month / 30 if total_submissions_month > 0 else 0

        if avg_daily > 0 and submissions_today > avg_daily * 3:
            anomalies.append({
                "type": "submission_spike",
                "severity": "info",
                "message": f"Unusually high submissions today ({submissions_today} vs avg {avg_daily:.1f})",
                "current": submissions_today,
                "average": round(avg_daily, 1)
            })
        elif avg_daily > 5 and submissions_today < avg_daily * 0.2:
            anomalies.append({
                "type": "submission_drop",
                "severity": "medium",
                "message": f"Very few submissions today ({submissions_today} vs avg {avg_daily:.1f})",
                "current": submissions_today,
                "average": round(avg_daily, 1)
            })

        # Check 3: Error spike detection
        error_stats = self.get_error_stats()
        if error_stats["has_spike"]:
            anomalies.append({
                "type": "error_spike",
                "severity": "high" if error_stats["error_change_percent"] > 100 else "medium",
                "message": f"Error rate increased {error_stats['error_change_percent']:.1f}% compared to last week",
                "this_week": error_stats["this_week_errors"],
                "last_week": error_stats["last_week_errors"],
                "change_percent": error_stats["error_change_percent"],
                "error_types": error_stats["error_types"]
            })

        # Check 4: High error installations
        if error_stats["installations_with_errors"] > 0:
            total_installations = self.db.query(
                func.count(distinct(Submission.installation_id))
            ).scalar() or 1
            error_rate = (error_stats["installations_with_errors"] / total_installations) * 100

            if error_rate > 30:
                anomalies.append({
                    "type": "high_error_rate",
                    "severity": "high" if error_rate > 50 else "medium",
                    "message": f"{error_rate:.1f}% of installations reporting errors",
                    "installations_with_errors": error_stats["installations_with_errors"],
                    "total_installations": total_installations,
                    "error_rate": round(error_rate, 1)
                })

        return {
            "anomalies": anomalies,
            "checked_at": now.isoformat(),
            "checks_performed": [
                "active_users_week_over_week",
                "daily_submission_volume",
                "error_spike_detection",
                "installation_error_rate"
            ]
        }

    def export_data(self, format: str = "json") -> Dict[str, Any]:
        """
        Export all dashboard data for external use.

        Args:
            format: Export format (json or csv)

        Returns:
            Dict with all exportable data
        """
        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "installations": self.get_installation_stats(days_trend=30),
            "deployment_modes": self.get_deployment_distribution(),
            "versions": self.get_version_distribution(limit=20),
            "geography": self.get_geography_distribution(limit=50),
            "printers": self.get_printer_stats(),
            "features": self.get_feature_usage(),
            "anomalies": self.get_anomalies()
        }

        return data

    def get_overview(self) -> Dict[str, Any]:
        """
        Get combined dashboard overview with all metrics.

        Returns:
            Dict with installations, deployment_modes, versions, geography, printers, features, anomalies
        """
        return {
            "installations": self.get_installation_stats(days_trend=30),
            "deployment_modes": self.get_deployment_distribution(),
            "versions": self.get_version_distribution(limit=10),
            "geography": self.get_geography_distribution(limit=20),
            "printers": self.get_printer_stats(),
            "features": self.get_feature_usage(),
            "anomalies": self.get_anomalies(),
            "last_updated": datetime.utcnow().isoformat()
        }
