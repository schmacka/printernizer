"""
Idea model for print ideas management.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class IdeaStatus(Enum):
    """Idea status enumeration."""
    IDEA = "idea"
    PLANNED = "planned"
    PRINTING = "printing"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class IdeaSourceType(Enum):
    """Idea source type enumeration."""
    MANUAL = "manual"
    MAKERWORLD = "makerworld"
    PRINTABLES = "printables"


@dataclass
class Idea:
    """Represents a print idea in the system."""
    id: str
    title: str
    description: Optional[str] = None
    source_type: str = "manual"
    source_url: Optional[str] = None
    thumbnail_path: Optional[str] = None
    category: Optional[str] = None
    priority: int = 3  # 1-5 scale
    status: str = "idea"
    is_business: bool = False
    estimated_print_time: Optional[int] = None  # in minutes
    material_notes: Optional[str] = None
    customer_info: Optional[str] = None
    planned_date: Optional[str] = None
    completed_date: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert idea to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'source_type': self.source_type,
            'source_url': self.source_url,
            'thumbnail_path': self.thumbnail_path,
            'category': self.category,
            'priority': self.priority,
            'status': self.status,
            'is_business': self.is_business,
            'estimated_print_time': self.estimated_print_time,
            'material_notes': self.material_notes,
            'customer_info': self.customer_info,
            'planned_date': self.planned_date,
            'completed_date': self.completed_date,
            'metadata': self.metadata,
            'tags': self.tags,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Idea':
        """Create idea from dictionary."""
        return cls(
            id=data['id'],
            title=data['title'],
            description=data.get('description'),
            source_type=data.get('source_type', 'manual'),
            source_url=data.get('source_url'),
            thumbnail_path=data.get('thumbnail_path'),
            category=data.get('category'),
            priority=data.get('priority', 3),
            status=data.get('status', 'idea'),
            is_business=data.get('is_business', False),
            estimated_print_time=data.get('estimated_print_time'),
            material_notes=data.get('material_notes'),
            customer_info=data.get('customer_info'),
            planned_date=data.get('planned_date'),
            completed_date=data.get('completed_date'),
            metadata=data.get('metadata'),
            tags=data.get('tags', []),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def validate(self) -> bool:
        """Validate idea data."""
        if not self.title:
            return False
        if self.priority < 1 or self.priority > 5:
            return False
        if self.status not in [s.value for s in IdeaStatus]:
            return False
        if self.source_type not in [s.value for s in IdeaSourceType]:
            return False
        return True

    def get_formatted_time(self) -> str:
        """Get formatted estimated print time."""
        if not self.estimated_print_time:
            return "Unknown"
        hours = self.estimated_print_time // 60
        minutes = self.estimated_print_time % 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"


@dataclass
class TrendingItem:
    """Represents a trending model from external platforms."""
    id: str
    platform: str
    model_id: str
    title: str
    url: str
    thumbnail_url: Optional[str] = None
    thumbnail_local_path: Optional[str] = None
    downloads: Optional[int] = None
    likes: Optional[int] = None
    creator: Optional[str] = None
    category: Optional[str] = None
    cached_at: Optional[str] = None
    expires_at: str = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert trending item to dictionary."""
        return {
            'id': self.id,
            'platform': self.platform,
            'model_id': self.model_id,
            'title': self.title,
            'url': self.url,
            'thumbnail_url': self.thumbnail_url,
            'thumbnail_local_path': self.thumbnail_local_path,
            'downloads': self.downloads,
            'likes': self.likes,
            'creator': self.creator,
            'category': self.category,
            'cached_at': self.cached_at,
            'expires_at': self.expires_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrendingItem':
        """Create trending item from dictionary."""
        return cls(
            id=data['id'],
            platform=data['platform'],
            model_id=data['model_id'],
            title=data['title'],
            url=data['url'],
            thumbnail_url=data.get('thumbnail_url'),
            thumbnail_local_path=data.get('thumbnail_local_path'),
            downloads=data.get('downloads'),
            likes=data.get('likes'),
            creator=data.get('creator'),
            category=data.get('category'),
            cached_at=data.get('cached_at'),
            expires_at=data['expires_at']
        )

    def is_expired(self) -> bool:
        """Check if the trending item has expired."""
        if not self.expires_at:
            return True
        expires = datetime.fromisoformat(self.expires_at)
        return datetime.now() > expires