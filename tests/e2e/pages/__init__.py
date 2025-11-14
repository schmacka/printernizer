"""Page Object Model imports"""
from .dashboard_page import DashboardPage
from .printers_page import PrintersPage
from .jobs_page import JobsPage
from .materials_page import MaterialsPage
from .settings_page import SettingsPage

__all__ = [
    "DashboardPage",
    "PrintersPage",
    "JobsPage",
    "MaterialsPage",
    "SettingsPage",
]
