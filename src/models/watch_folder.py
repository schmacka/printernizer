"""
Watch folder data model for persistent storage.
Represents a directory monitored for 3D print files.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class WatchFolderSource(str, Enum):
    """Source of how the watch folder was added."""
    MANUAL = "manual"
    ENV_MIGRATION = "env_migration" 
    IMPORT = "import"


@dataclass
class WatchFolder:
    """Watch folder data model."""
    id: Optional[int] = None
    folder_path: str = ""
    is_active: bool = True
    recursive: bool = True
    
    # Folder information
    folder_name: Optional[str] = None
    description: Optional[str] = None
    
    # Monitoring statistics
    file_count: int = 0
    last_scan_at: Optional[datetime] = None
    
    # Error handling
    is_valid: bool = True
    validation_error: Optional[str] = None
    last_validation_at: Optional[datetime] = None
    
    # Source tracking
    source: WatchFolderSource = WatchFolderSource.MANUAL
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'folder_path': self.folder_path,
            'is_active': self.is_active,
            'recursive': self.recursive,
            'folder_name': self.folder_name,
            'description': self.description,
            'file_count': self.file_count,
            'last_scan_at': self.last_scan_at.isoformat() if self.last_scan_at else None,
            'is_valid': self.is_valid,
            'validation_error': self.validation_error,
            'last_validation_at': self.last_validation_at.isoformat() if self.last_validation_at else None,
            'source': self.source.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WatchFolder':
        """Create instance from dictionary."""
        return cls(
            id=data.get('id'),
            folder_path=data.get('folder_path', ''),
            is_active=bool(data.get('is_active', True)),
            recursive=bool(data.get('recursive', True)),
            folder_name=data.get('folder_name'),
            description=data.get('description'),
            file_count=int(data.get('file_count', 0)),
            last_scan_at=datetime.fromisoformat(data['last_scan_at']) if data.get('last_scan_at') else None,
            is_valid=bool(data.get('is_valid', True)),
            validation_error=data.get('validation_error'),
            last_validation_at=datetime.fromisoformat(data['last_validation_at']) if data.get('last_validation_at') else None,
            source=WatchFolderSource(data.get('source', WatchFolderSource.MANUAL.value)),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'WatchFolder':
        """Create instance from database row."""
        return cls(
            id=row[0],
            folder_path=row[1],
            is_active=bool(row[2]),
            recursive=bool(row[3]),
            folder_name=row[4],
            description=row[5],
            file_count=int(row[6]),
            last_scan_at=datetime.fromisoformat(row[7]) if row[7] else None,
            is_valid=bool(row[8]),
            validation_error=row[9],
            last_validation_at=datetime.fromisoformat(row[10]) if row[10] else None,
            source=WatchFolderSource(row[11]),
            created_at=datetime.fromisoformat(row[12]) if row[12] else None,
            updated_at=datetime.fromisoformat(row[13]) if row[13] else None
        )
    
    def get_display_name(self) -> str:
        """Get display name for the folder."""
        if self.folder_name:
            return self.folder_name
        
        # Extract folder name from path
        import os
        return os.path.basename(self.folder_path) or self.folder_path
    
    def is_accessible(self) -> bool:
        """Check if folder is currently accessible."""
        import os
        return os.path.exists(self.folder_path) and os.path.isdir(self.folder_path)