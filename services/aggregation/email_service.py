"""
Email service for sending usage statistics reports.

Provides functionality to send weekly summary and monthly reports
via SMTP email.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email reports via SMTP."""

    def __init__(self):
        """Initialize the email service."""
        self.enabled = settings.smtp_enabled
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.username = settings.smtp_username
        self.password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name
        self.use_tls = settings.smtp_use_tls
        self.use_ssl = settings.smtp_use_ssl
        self.recipients = settings.report_recipients

    def is_configured(self) -> bool:
        """Check if SMTP is properly configured."""
        return (
            self.enabled and
            bool(self.host) and
            bool(self.username) and
            bool(self.password) and
            bool(self.from_email) and
            len(self.recipients) > 0
        )

    def send_email(
        self,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        recipients: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send an email via SMTP.

        Args:
            subject: Email subject line
            html_content: HTML body content
            text_content: Plain text body (optional fallback)
            recipients: Override default recipients

        Returns:
            Dict with success status and any error message
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "SMTP is not configured. Set SMTP_ENABLED=true and configure SMTP settings."
            }

        to_addresses = recipients or self.recipients
        if not to_addresses:
            return {
                "success": False,
                "error": "No recipients configured"
            }

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = ", ".join(to_addresses)

            # Add plain text part
            if text_content:
                part1 = MIMEText(text_content, "plain")
                msg.attach(part1)

            # Add HTML part
            part2 = MIMEText(html_content, "html")
            msg.attach(part2)

            # Connect and send
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.host, self.port)
            else:
                server = smtplib.SMTP(self.host, self.port)
                if self.use_tls:
                    server.starttls()

            server.login(self.username, self.password)
            server.sendmail(self.from_email, to_addresses, msg.as_string())
            server.quit()

            logger.info(f"Email sent successfully to {len(to_addresses)} recipients")
            return {
                "success": True,
                "recipients": to_addresses
            }

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return {
                "success": False,
                "error": "SMTP authentication failed. Check username and password."
            }
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return {
                "success": False,
                "error": f"SMTP error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return {
                "success": False,
                "error": f"Failed to send email: {str(e)}"
            }


class ReportGenerator:
    """Generates HTML email reports from analytics data."""

    @staticmethod
    def generate_weekly_summary(data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate a weekly summary email from analytics data.

        Args:
            data: Analytics data containing overview, anomalies, trends

        Returns:
            Dict with 'subject', 'html', and 'text' keys
        """
        overview = data.get("overview", {})
        anomalies = data.get("anomalies", [])
        trends = data.get("trends", {})

        # Calculate week dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        subject = f"Printernizer Weekly Stats Summary - {end_date.strftime('%b %d, %Y')}"

        # Build HTML content
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            color: white;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 24px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .header p {{
            margin: 8px 0 0;
            opacity: 0.9;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 32px;
            font-weight: 700;
            color: #3b82f6;
            line-height: 1;
        }}
        .stat-number.positive {{
            color: #10b981;
        }}
        .stat-number.negative {{
            color: #ef4444;
        }}
        .stat-label {{
            font-size: 12px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 8px;
        }}
        .section {{
            margin-bottom: 24px;
        }}
        .section h2 {{
            font-size: 18px;
            color: #1e293b;
            margin: 0 0 12px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e2e8f0;
        }}
        .alert {{
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 8px;
        }}
        .alert-high {{
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #dc2626;
        }}
        .alert-medium {{
            background: #fffbeb;
            border: 1px solid #fde68a;
            color: #d97706;
        }}
        .alert-info {{
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            color: #2563eb;
        }}
        .alert-ok {{
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            color: #16a34a;
        }}
        .footer {{
            text-align: center;
            font-size: 12px;
            color: #94a3b8;
            padding-top: 24px;
            border-top: 1px solid #e2e8f0;
        }}
        .trend-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #f1f5f9;
        }}
        .trend-item:last-child {{
            border-bottom: none;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Printernizer Weekly Summary</h1>
        <p>{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{overview.get('total_installations', 0):,}</div>
            <div class="stat-label">Total Installations</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{overview.get('active_7d', 0):,}</div>
            <div class="stat-label">Active (7 Days)</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{overview.get('active_30d', 0):,}</div>
            <div class="stat-label">Active (30 Days)</div>
        </div>
        <div class="stat-card">
            <div class="stat-number {'positive' if overview.get('growth_7d_percent', 0) >= 0 else 'negative'}">{overview.get('growth_7d_percent', 0):+.1f}%</div>
            <div class="stat-label">7-Day Growth</div>
        </div>
    </div>
"""

        # Anomalies section
        if anomalies:
            html += """
    <div class="section">
        <h2>Alerts &amp; Anomalies</h2>
"""
            for anomaly in anomalies:
                severity = anomaly.get("severity", "info")
                html += f"""
        <div class="alert alert-{severity}">
            <strong>{anomaly.get('type', 'Unknown').replace('_', ' ').title()}:</strong>
            {anomaly.get('message', '')}
        </div>
"""
            html += "    </div>\n"
        else:
            html += """
    <div class="section">
        <h2>Alerts &amp; Anomalies</h2>
        <div class="alert alert-ok">
            All metrics are within normal ranges. No anomalies detected.
        </div>
    </div>
"""

        # Version distribution
        versions = overview.get("top_versions", [])
        if versions:
            html += """
    <div class="section">
        <h2>Top Versions</h2>
"""
            for v in versions[:5]:
                html += f"""
        <div class="trend-item">
            <span>v{v.get('version', 'Unknown')}</span>
            <span><strong>{v.get('count', 0):,}</strong> ({v.get('percentage', 0):.1f}%)</span>
        </div>
"""
            html += "    </div>\n"

        # Footer
        html += f"""
    <div class="footer">
        <p>This is an automated report from Printernizer Usage Statistics</p>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>
</body>
</html>
"""

        # Plain text version
        text = f"""
Printernizer Weekly Summary
{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}

KEY METRICS
-----------
Total Installations: {overview.get('total_installations', 0):,}
Active (7 Days): {overview.get('active_7d', 0):,}
Active (30 Days): {overview.get('active_30d', 0):,}
7-Day Growth: {overview.get('growth_7d_percent', 0):+.1f}%

"""

        if anomalies:
            text += "ALERTS & ANOMALIES\n------------------\n"
            for anomaly in anomalies:
                text += f"- [{anomaly.get('severity', 'info').upper()}] {anomaly.get('type', 'Unknown')}: {anomaly.get('message', '')}\n"
            text += "\n"
        else:
            text += "ALERTS & ANOMALIES\n------------------\nAll metrics are within normal ranges.\n\n"

        if versions:
            text += "TOP VERSIONS\n------------\n"
            for v in versions[:5]:
                text += f"- v{v.get('version', 'Unknown')}: {v.get('count', 0):,} ({v.get('percentage', 0):.1f}%)\n"

        text += f"\n---\nGenerated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"

        return {
            "subject": subject,
            "html": html,
            "text": text
        }

    @staticmethod
    def generate_monthly_report(data: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate a comprehensive monthly report from analytics data.

        Args:
            data: Analytics data containing all metrics

        Returns:
            Dict with 'subject', 'html', and 'text' keys
        """
        overview = data.get("overview", {})
        anomalies = data.get("anomalies", [])
        deployment = data.get("deployment_modes", [])
        geography = data.get("geography", [])
        features = data.get("features", [])

        # Calculate month info
        now = datetime.now()
        month_name = now.strftime("%B %Y")

        subject = f"Printernizer Monthly Report - {month_name}"

        # Build HTML content
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 700px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #8b5cf6, #6d28d9);
            color: white;
            padding: 40px 30px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 24px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .header p {{
            margin: 8px 0 0;
            opacity: 0.9;
            font-size: 16px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 24px;
            font-weight: 700;
            color: #8b5cf6;
            line-height: 1;
        }}
        .stat-number.positive {{
            color: #10b981;
        }}
        .stat-number.negative {{
            color: #ef4444;
        }}
        .stat-label {{
            font-size: 11px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 8px;
        }}
        .section {{
            margin-bottom: 24px;
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
        }}
        .section h2 {{
            font-size: 16px;
            color: #1e293b;
            margin: 0 0 16px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e2e8f0;
        }}
        .progress-bar {{
            background: #e2e8f0;
            border-radius: 4px;
            height: 8px;
            margin-top: 4px;
        }}
        .progress-fill {{
            background: #8b5cf6;
            border-radius: 4px;
            height: 100%;
        }}
        .item-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #f1f5f9;
        }}
        .item-row:last-child {{
            border-bottom: none;
        }}
        .item-name {{
            font-weight: 500;
        }}
        .item-value {{
            color: #64748b;
        }}
        .footer {{
            text-align: center;
            font-size: 12px;
            color: #94a3b8;
            padding-top: 24px;
            border-top: 1px solid #e2e8f0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Monthly Report</h1>
        <p>{month_name}</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{overview.get('total_installations', 0):,}</div>
            <div class="stat-label">Total Installs</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{overview.get('active_7d', 0):,}</div>
            <div class="stat-label">Active (7d)</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{overview.get('active_30d', 0):,}</div>
            <div class="stat-label">Active (30d)</div>
        </div>
        <div class="stat-card">
            <div class="stat-number {'positive' if overview.get('growth_7d_percent', 0) >= 0 else 'negative'}">{overview.get('growth_7d_percent', 0):+.1f}%</div>
            <div class="stat-label">Growth</div>
        </div>
    </div>
"""

        # Deployment modes section
        if deployment:
            html += """
    <div class="section">
        <h2>Deployment Distribution</h2>
"""
            total = sum(d.get('count', 0) for d in deployment)
            for d in deployment:
                pct = (d.get('count', 0) / total * 100) if total > 0 else 0
                html += f"""
        <div class="item-row">
            <span class="item-name">{d.get('mode', 'Unknown').replace('_', ' ').title()}</span>
            <span class="item-value">{d.get('count', 0):,} ({pct:.1f}%)</span>
        </div>
        <div class="progress-bar"><div class="progress-fill" style="width: {pct}%"></div></div>
"""
            html += "    </div>\n"

        # Geography section
        if geography:
            html += """
    <div class="section">
        <h2>Geographic Distribution (Top 10)</h2>
"""
            for g in geography[:10]:
                html += f"""
        <div class="item-row">
            <span class="item-name">{g.get('country', 'Unknown')}</span>
            <span class="item-value">{g.get('count', 0):,} ({g.get('percentage', 0):.1f}%)</span>
        </div>
"""
            html += "    </div>\n"

        # Feature usage section
        if features:
            html += """
    <div class="section">
        <h2>Feature Adoption</h2>
"""
            for f in features:
                pct = f.get('adoption_rate', 0)
                html += f"""
        <div class="item-row">
            <span class="item-name">{f.get('feature', 'Unknown').replace('_', ' ').title()}</span>
            <span class="item-value">{pct:.1f}% adoption</span>
        </div>
        <div class="progress-bar"><div class="progress-fill" style="width: {pct}%"></div></div>
"""
            html += "    </div>\n"

        # Footer
        html += f"""
    <div class="footer">
        <p>Printernizer Usage Statistics - Monthly Report</p>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    </div>
</body>
</html>
"""

        # Plain text version
        text = f"""
PRINTERNIZER MONTHLY REPORT
{month_name}
{'=' * 40}

KEY METRICS
-----------
Total Installations: {overview.get('total_installations', 0):,}
Active (7 Days): {overview.get('active_7d', 0):,}
Active (30 Days): {overview.get('active_30d', 0):,}
Growth: {overview.get('growth_7d_percent', 0):+.1f}%

"""

        if deployment:
            text += "DEPLOYMENT DISTRIBUTION\n-----------------------\n"
            total = sum(d.get('count', 0) for d in deployment)
            for d in deployment:
                pct = (d.get('count', 0) / total * 100) if total > 0 else 0
                text += f"- {d.get('mode', 'Unknown')}: {d.get('count', 0):,} ({pct:.1f}%)\n"
            text += "\n"

        if geography:
            text += "GEOGRAPHIC DISTRIBUTION (Top 10)\n--------------------------------\n"
            for g in geography[:10]:
                text += f"- {g.get('country', 'Unknown')}: {g.get('count', 0):,} ({g.get('percentage', 0):.1f}%)\n"
            text += "\n"

        if features:
            text += "FEATURE ADOPTION\n----------------\n"
            for f in features:
                text += f"- {f.get('feature', 'Unknown')}: {f.get('adoption_rate', 0):.1f}% adoption\n"

        text += f"\n---\nGenerated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"

        return {
            "subject": subject,
            "html": html,
            "text": text
        }


# Global instances
email_service = EmailService()
report_generator = ReportGenerator()
