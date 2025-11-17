"""Idea repository for database operations.

This repository handles all idea-related database operations including
idea management, tags, and statistics.
"""

import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional
import structlog

from .base_repository import BaseRepository


logger = structlog.get_logger(__name__)


class IdeaRepository(BaseRepository):
    """Repository for idea-related database operations.

    Handles CRUD operations for print ideas, including status management,
    tagging, and analytics.
    """

    async def create(self, idea_data: Dict[str, Any]) -> bool:
        """Create a new idea record.

        Args:
            idea_data: Dictionary containing idea information with keys:
                - id: Unique idea identifier (required)
                - title: Idea title (required)
                - description: Detailed description
                - source_type: Source of idea (default: 'manual')
                - source_url: URL if from external source
                - thumbnail_path: Path to thumbnail image
                - category: Idea category
                - priority: Priority level 1-5 (default: 3)
                - status: Idea status (default: 'idea')
                - is_business: Business order flag (default: False)
                - estimated_print_time: Estimated duration in minutes
                - material_notes: Material requirements notes
                - customer_info: Customer information for business orders
                - planned_date: Planned execution date
                - metadata: JSON serializable metadata

        Returns:
            True if idea was created successfully, False otherwise
        """
        try:
            await self._execute_write(
                """INSERT INTO ideas (id, title, description, source_type, source_url, thumbnail_path,
                                    category, priority, status, is_business, estimated_print_time,
                                    material_notes, customer_info, planned_date, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    idea_data['id'],
                    idea_data['title'],
                    idea_data.get('description'),
                    idea_data.get('source_type', 'manual'),
                    idea_data.get('source_url'),
                    idea_data.get('thumbnail_path'),
                    idea_data.get('category'),
                    idea_data.get('priority', 3),
                    idea_data.get('status', 'idea'),
                    idea_data.get('is_business', False),
                    idea_data.get('estimated_print_time'),
                    idea_data.get('material_notes'),
                    idea_data.get('customer_info'),
                    idea_data.get('planned_date'),
                    idea_data.get('metadata')
                )
            )
            return True
        except sqlite3.IntegrityError as e:
            error_msg = str(e).lower()
            if 'unique' in error_msg:
                logger.info("Duplicate idea detected (UNIQUE constraint)", idea_id=idea_data.get('id'))
                return False
            raise
        except Exception as e:
            logger.error("Failed to create idea", idea_id=idea_data.get('id'), error=str(e), exc_info=True)
            return False

    async def get(self, idea_id: str) -> Optional[Dict[str, Any]]:
        """Get idea by ID.

        Args:
            idea_id: Unique idea identifier

        Returns:
            Idea dictionary with all fields, or None if not found
        """
        try:
            return await self._fetch_one("SELECT * FROM ideas WHERE id = ?", (idea_id,))
        except Exception as e:
            logger.error("Failed to get idea", idea_id=idea_id, error=str(e), exc_info=True)
            return None

    async def list(self, status: Optional[str] = None, is_business: Optional[bool] = None,
                   category: Optional[str] = None, source_type: Optional[str] = None,
                   limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """List ideas with optional filtering and pagination.

        Args:
            status: Filter by status ('idea', 'planned', 'printing', 'completed', 'archived')
            is_business: Filter by business flag (True/False)
            category: Filter by category
            source_type: Filter by source type ('manual', 'trending', 'url', etc.)
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)

        Returns:
            List of idea dictionaries ordered by priority DESC, created_at DESC

        Notes:
            - Returns empty list on error
        """
        try:
            query = "SELECT * FROM ideas"
            params = []
            conditions = []

            if status:
                conditions.append("status = ?")
                params.append(status)
            if is_business is not None:
                conditions.append("is_business = ?")
                params.append(int(is_business))
            if category:
                conditions.append("category = ?")
                params.append(category)
            if source_type:
                conditions.append("source_type = ?")
                params.append(source_type)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY priority DESC, created_at DESC"

            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
                if offset is not None:
                    query += " OFFSET ?"
                    params.append(offset)

            return await self._fetch_all(query, tuple(params))
        except Exception as e:
            logger.error("Failed to list ideas", error=str(e), exc_info=True)
            return []

    async def update(self, idea_id: str, updates: Dict[str, Any]) -> bool:
        """Update idea with provided fields.

        Args:
            idea_id: Unique idea identifier
            updates: Dictionary of fields to update

        Returns:
            True if update succeeded, False otherwise

        Notes:
            - Protects immutable fields (id, created_at)
            - Automatically updates updated_at timestamp
        """
        try:
            set_clauses = []
            params = []

            for field, value in updates.items():
                if field not in ['id', 'created_at']:
                    set_clauses.append(f"{field} = ?")
                    params.append(value)

            if not set_clauses:
                return True  # Nothing to update

            set_clauses.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(idea_id)

            query = f"UPDATE ideas SET {', '.join(set_clauses)} WHERE id = ?"
            await self._execute_write(query, tuple(params))
            return True
        except Exception as e:
            logger.error("Failed to update idea", idea_id=idea_id, error=str(e), exc_info=True)
            return False

    async def delete(self, idea_id: str) -> bool:
        """Delete an idea record.

        Args:
            idea_id: Unique idea identifier

        Returns:
            True if deletion succeeded, False otherwise

        Notes:
            - Automatically deletes associated tags from idea_tags table
            - Uses cascading delete to maintain referential integrity
        """
        try:
            # First delete associated tags
            await self._execute_write("DELETE FROM idea_tags WHERE idea_id = ?", (idea_id,))
            # Then delete the idea
            await self._execute_write("DELETE FROM ideas WHERE id = ?", (idea_id,))
            return True
        except Exception as e:
            logger.error("Failed to delete idea", idea_id=idea_id, error=str(e), exc_info=True)
            return False

    async def update_status(self, idea_id: str, status: str) -> bool:
        """Update idea status.

        Args:
            idea_id: Unique idea identifier
            status: New status ('idea', 'planned', 'printing', 'completed', 'archived')

        Returns:
            True if status update succeeded, False otherwise

        Notes:
            - Automatically sets completed_date when status changes to 'completed'
        """
        updates = {'status': status}
        if status == 'completed':
            updates['completed_date'] = datetime.now().isoformat()
        return await self.update(idea_id, updates)

    async def add_tags(self, idea_id: str, tags: List[str]) -> bool:
        """Add tags to an idea.

        Args:
            idea_id: Unique idea identifier
            tags: List of tag strings to add

        Returns:
            True if all tags were added successfully, False otherwise

        Notes:
            - Uses INSERT OR IGNORE to handle duplicate tags gracefully
            - Tags are case-sensitive
        """
        try:
            for tag in tags:
                await self._execute_write(
                    "INSERT OR IGNORE INTO idea_tags (idea_id, tag) VALUES (?, ?)",
                    (idea_id, tag)
                )
            return True
        except Exception as e:
            logger.error("Failed to add idea tags", idea_id=idea_id, tags=tags, error=str(e), exc_info=True)
            return False

    async def remove_tags(self, idea_id: str, tags: List[str]) -> bool:
        """Remove tags from an idea.

        Args:
            idea_id: Unique idea identifier
            tags: List of tag strings to remove

        Returns:
            True if all tags were removed successfully, False otherwise
        """
        try:
            for tag in tags:
                await self._execute_write(
                    "DELETE FROM idea_tags WHERE idea_id = ? AND tag = ?",
                    (idea_id, tag)
                )
            return True
        except Exception as e:
            logger.error("Failed to remove idea tags", idea_id=idea_id, tags=tags, error=str(e), exc_info=True)
            return False

    async def get_tags(self, idea_id: str) -> List[str]:
        """Get all tags for an idea.

        Args:
            idea_id: Unique idea identifier

        Returns:
            List of tag strings, empty list if no tags or on error
        """
        try:
            rows = await self._fetch_all(
                "SELECT tag FROM idea_tags WHERE idea_id = ?",
                (idea_id,)
            )
            return [row['tag'] for row in rows]
        except Exception as e:
            logger.error("Failed to get idea tags", idea_id=idea_id, error=str(e), exc_info=True)
            return []

    async def get_all_tags(self) -> List[Dict[str, Any]]:
        """Get all unique tags with usage counts.

        Returns:
            List of dictionaries with 'tag' and 'count' keys, ordered by count DESC

        Notes:
            - Returns empty list on error
        """
        try:
            rows = await self._fetch_all(
                "SELECT tag, COUNT(*) as count FROM idea_tags GROUP BY tag ORDER BY count DESC",
                ()
            )
            return rows
        except Exception as e:
            logger.error("Failed to get all tags", error=str(e), exc_info=True)
            return []

    async def exists(self, idea_id: str) -> bool:
        """Check if an idea exists.

        Args:
            idea_id: Unique idea identifier

        Returns:
            True if idea exists, False otherwise
        """
        try:
            result = await self._fetch_one("SELECT 1 FROM ideas WHERE id = ?", (idea_id,))
            return result is not None
        except Exception as e:
            logger.error("Failed to check idea existence", idea_id=idea_id, error=str(e), exc_info=True)
            return False

    async def get_statistics(self) -> Dict[str, Any]:
        """Get idea statistics.

        Returns:
            Dictionary with statistics including:
                - {status}_count: Count of ideas by status
                - business_ideas: Count of business ideas
                - personal_ideas: Count of personal ideas
                - {source_type}_count: Count of ideas by source type
                - total_ideas: Total count of all ideas
                - avg_priority: Average priority of all ideas

        Notes:
            - Returns empty dict on error
        """
        try:
            stats = {}

            # Status counts
            rows = await self._fetch_all(
                "SELECT status, COUNT(*) as count FROM ideas GROUP BY status",
                ()
            )
            for row in rows:
                stats[f"{row['status']}_count"] = row['count']

            # Business vs Personal counts
            rows = await self._fetch_all(
                "SELECT is_business, COUNT(*) as count FROM ideas GROUP BY is_business",
                ()
            )
            for row in rows:
                key = "business_ideas" if row['is_business'] else "personal_ideas"
                stats[key] = row['count']

            # Source type counts
            rows = await self._fetch_all(
                "SELECT source_type, COUNT(*) as count FROM ideas GROUP BY source_type",
                ()
            )
            for row in rows:
                stats[f"{row['source_type']}_count"] = row['count']

            # Total ideas
            row = await self._fetch_one("SELECT COUNT(*) as total FROM ideas", ())
            stats['total_ideas'] = row['total'] if row else 0

            # Average priority
            row = await self._fetch_one("SELECT AVG(priority) as avg_priority FROM ideas WHERE priority IS NOT NULL", ())
            stats['avg_priority'] = round(row['avg_priority'], 2) if row and row['avg_priority'] else 0

            return stats
        except Exception as e:
            logger.error("Failed to get idea statistics", error=str(e), exc_info=True)
            return {}
