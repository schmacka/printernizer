"""
Database repositories for the repository pattern.

This package contains specialized repository classes that encapsulate
database operations for specific domain entities.
"""
from .base_repository import BaseRepository
from .printer_repository import PrinterRepository

__all__ = [
    'BaseRepository',
    'PrinterRepository',
]
