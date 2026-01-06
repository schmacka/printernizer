"""Page Object Model imports"""
from .base_page import BasePage
from .dashboard_page import DashboardPage
from .printers_page import PrintersPage
from .jobs_page import JobsPage
from .materials_page import MaterialsPage
from .settings_page import SettingsPage
from .statistics_page import StatisticsPage
from .timelapses_page import TimelapsesPage
from .files_page import FilesPage
from .library_page import LibraryPage
from .ideas_page import IdeasPage
from .debug_page import DebugPage

__all__ = [
    "BasePage",
    "DashboardPage",
    "PrintersPage",
    "JobsPage",
    "MaterialsPage",
    "SettingsPage",
    "StatisticsPage",
    "TimelapsesPage",
    "FilesPage",
    "LibraryPage",
    "IdeasPage",
    "DebugPage",
]
