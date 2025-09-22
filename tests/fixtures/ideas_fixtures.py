"""
Test fixtures for Ideas feature.
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List


def create_sample_idea(
    title: str = "Test Idea",
    status: str = "idea",
    priority: int = 3,
    is_business: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """Create a sample idea for testing."""
    idea_data = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": f"Description for {title}",
        "source_type": "manual",
        "category": "prototype",
        "priority": priority,
        "status": status,
        "is_business": is_business,
        "estimated_print_time": 120,  # 2 hours
        "material_notes": "PLA, 0.2mm layer height",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    # Override with any provided kwargs
    idea_data.update(kwargs)
    return idea_data


def create_sample_trending_item(
    platform: str = "printables",
    **kwargs
) -> Dict[str, Any]:
    """Create a sample trending item for testing."""
    expires_at = datetime.now() + timedelta(hours=6)

    trending_data = {
        "id": f"{platform}_{uuid.uuid4()}",
        "platform": platform,
        "model_id": str(uuid.uuid4()),
        "title": f"Trending Model from {platform.title()}",
        "url": f"https://{platform}.com/model/123",
        "thumbnail_url": f"https://{platform}.com/thumb/123.jpg",
        "downloads": 1250,
        "likes": 95,
        "creator": "TestCreator",
        "category": "functional",
        "cached_at": datetime.now().isoformat(),
        "expires_at": expires_at.isoformat()
    }

    # Override with any provided kwargs
    trending_data.update(kwargs)
    return trending_data


class IdeasTestFixtures:
    """Collection of test fixtures for Ideas feature."""

    @staticmethod
    def get_sample_ideas() -> List[Dict[str, Any]]:
        """Get a collection of sample ideas for testing."""
        return [
            create_sample_idea(
                title="iPhone Case Redesign",
                description="Custom iPhone case with improved grip",
                category="product",
                priority=4,
                is_business=True,
                customer_info="Client: Tech Startup Inc.",
                estimated_print_time=45
            ),
            create_sample_idea(
                title="Garden Tool Organizer",
                description="Wall-mounted organizer for garden tools",
                category="functional",
                priority=2,
                status="planned",
                planned_date=(datetime.now() + timedelta(days=3)).date().isoformat()
            ),
            create_sample_idea(
                title="Birthday Gift Miniature",
                description="Custom miniature figure for birthday gift",
                category="gift",
                priority=5,
                status="printing",
                estimated_print_time=180
            ),
            create_sample_idea(
                title="Desk Cable Management",
                description="Custom cable management solution for standing desk",
                category="functional",
                priority=3,
                status="completed",
                completed_date=datetime.now().date().isoformat()
            ),
            create_sample_idea(
                title="Business Card Holder",
                description="Professional business card display stand",
                category="business",
                priority=3,
                is_business=True,
                status="archived"
            )
        ]

    @staticmethod
    def get_sample_trending_items() -> List[Dict[str, Any]]:
        """Get a collection of sample trending items for testing."""
        return [
            create_sample_trending_item(
                platform="printables",
                title="Articulated Dragon",
                downloads=5420,
                likes=387,
                category="artistic",
                creator="DragonMaker3D"
            ),
            create_sample_trending_item(
                platform="makerworld",
                title="Phone Stand Adjustable",
                downloads=2890,
                likes=156,
                category="functional",
                creator="UtilityDesigns"
            ),
            create_sample_trending_item(
                platform="printables",
                title="Spiral Vase Collection",
                downloads=1820,
                likes=203,
                category="decorative",
                creator="VaseArtist"
            ),
            create_sample_trending_item(
                platform="makerworld",
                title="Raspberry Pi Case v2",
                downloads=3240,
                likes=278,
                category="functional",
                creator="TechEnclosures"
            )
        ]

    @staticmethod
    def get_sample_tags() -> List[str]:
        """Get a collection of sample tags for testing."""
        return [
            "prototype", "gift", "business", "functional", "decorative",
            "artistic", "urgent", "client-work", "personal", "experimental",
            "pla", "petg", "tpu", "miniature", "large-print", "multi-part"
        ]

    @staticmethod
    def get_sample_categories() -> List[str]:
        """Get a collection of sample categories for testing."""
        return [
            "prototype", "product", "gift", "business", "functional",
            "decorative", "artistic", "tool", "organizer", "case",
            "holder", "mount", "replacement", "upgrade", "toy"
        ]


def create_idea_with_tags(
    title: str,
    tags: List[str],
    **kwargs
) -> Dict[str, Any]:
    """Create an idea with specific tags."""
    idea = create_sample_idea(title=title, **kwargs)
    idea["tags"] = tags
    return idea


def create_business_idea(
    title: str,
    customer_name: str,
    **kwargs
) -> Dict[str, Any]:
    """Create a business idea with customer information."""
    idea = create_sample_idea(
        title=title,
        is_business=True,
        customer_info=f"Customer: {customer_name}",
        **kwargs
    )
    return idea


def create_external_idea(
    title: str,
    platform: str,
    url: str,
    **kwargs
) -> Dict[str, Any]:
    """Create an idea imported from external platform."""
    idea = create_sample_idea(
        title=title,
        source_type=platform,
        source_url=url,
        metadata={
            "platform": platform,
            "imported_at": datetime.now().isoformat(),
            "original_creator": "ExternalCreator"
        },
        **kwargs
    )
    return idea