"""
Tags API Router - File tag management endpoints.
Provides REST API for tag CRUD operations and file-tag assignments.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Path as PathParam
from pydantic import BaseModel, Field
import structlog
import uuid
from datetime import datetime

from src.utils.errors import (
    NotFoundError,
    ValidationError as PrinternizerValidationError,
    success_response
)
from src.database.database import get_db

logger = structlog.get_logger()

# Create router - use empty string for root per API routing standards
router = APIRouter(prefix="/tags", tags=["tags"])


# Pydantic models
class TagBase(BaseModel):
    """Base tag model."""
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    color: Optional[str] = Field("#6b7280", pattern=r"^#[0-9a-fA-F]{6}$", description="Hex color code")
    description: Optional[str] = Field(None, max_length=200, description="Tag description")


class TagCreate(TagBase):
    """Model for creating a new tag."""
    pass


class TagUpdate(BaseModel):
    """Model for updating an existing tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    description: Optional[str] = Field(None, max_length=200)


class TagResponse(TagBase):
    """Tag response model."""
    id: str
    usage_count: int = 0
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TagListResponse(BaseModel):
    """Tag list response."""
    tags: List[TagResponse]
    total: int


class FileTagAssignment(BaseModel):
    """Model for assigning/removing tags from files."""
    file_checksum: str = Field(..., description="File checksum to tag")
    tag_ids: List[str] = Field(..., min_length=1, description="List of tag IDs")


class FileTagsResponse(BaseModel):
    """Response for file tags."""
    file_checksum: str
    tags: List[TagResponse]


# Helper functions
def _row_to_tag(row) -> TagResponse:
    """Convert database row to TagResponse."""
    return TagResponse(
        id=row["id"],
        name=row["name"],
        color=row["color"] or "#6b7280",
        description=row["description"],
        usage_count=row["usage_count"],
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"])
    )


# ==================== TAG CRUD ENDPOINTS ====================

@router.get("", response_model=TagListResponse)
async def list_tags(
    sort_by: str = Query("name", enum=["name", "usage_count", "created_at"]),
    sort_order: str = Query("asc", enum=["asc", "desc"])
):
    """
    List all available tags.

    Returns all tags sorted by the specified field.
    """
    try:
        db = await get_db()

        order_direction = "DESC" if sort_order == "desc" else "ASC"
        query = f"""
            SELECT * FROM file_tags
            ORDER BY {sort_by} {order_direction}
        """

        rows = await db.fetch_all(query)
        tags = [_row_to_tag(row) for row in rows]

        return TagListResponse(tags=tags, total=len(tags))

    except Exception as e:
        logger.error("Failed to list tags", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve tags")


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(tag_id: str = PathParam(..., description="Tag ID")):
    """Get a specific tag by ID."""
    try:
        db = await get_db()

        row = await db.fetch_one(
            "SELECT * FROM file_tags WHERE id = ?",
            (tag_id,)
        )

        if not row:
            raise NotFoundError(f"Tag not found: {tag_id}")

        return _row_to_tag(row)

    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Tag not found: {tag_id}")
    except Exception as e:
        logger.error("Failed to get tag", tag_id=tag_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve tag")


@router.post("", response_model=TagResponse, status_code=201)
async def create_tag(tag: TagCreate):
    """
    Create a new tag.

    Tag names must be unique (case-insensitive).
    """
    try:
        db = await get_db()

        # Check for duplicate name
        existing = await db.fetch_one(
            "SELECT id FROM file_tags WHERE LOWER(name) = LOWER(?)",
            (tag.name,)
        )
        if existing:
            raise PrinternizerValidationError(f"Tag with name '{tag.name}' already exists")

        tag_id = f"tag_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()

        await db.execute(
            """
            INSERT INTO file_tags (id, name, color, description, usage_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, 0, ?, ?)
            """,
            (tag_id, tag.name, tag.color, tag.description, now, now)
        )

        logger.info("Created tag", tag_id=tag_id, name=tag.name)

        return TagResponse(
            id=tag_id,
            name=tag.name,
            color=tag.color or "#6b7280",
            description=tag.description,
            usage_count=0,
            created_at=now,
            updated_at=now
        )

    except PrinternizerValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to create tag", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create tag")


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: str = PathParam(..., description="Tag ID"),
    tag: TagUpdate = None
):
    """Update an existing tag."""
    try:
        db = await get_db()

        # Verify tag exists
        existing = await db.fetch_one(
            "SELECT * FROM file_tags WHERE id = ?",
            (tag_id,)
        )
        if not existing:
            raise NotFoundError(f"Tag not found: {tag_id}")

        # Check for duplicate name if updating name
        if tag.name and tag.name.lower() != existing["name"].lower():
            duplicate = await db.fetch_one(
                "SELECT id FROM file_tags WHERE LOWER(name) = LOWER(?) AND id != ?",
                (tag.name, tag_id)
            )
            if duplicate:
                raise PrinternizerValidationError(f"Tag with name '{tag.name}' already exists")

        # Build update query
        updates = []
        params = []
        if tag.name is not None:
            updates.append("name = ?")
            params.append(tag.name)
        if tag.color is not None:
            updates.append("color = ?")
            params.append(tag.color)
        if tag.description is not None:
            updates.append("description = ?")
            params.append(tag.description)

        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.utcnow().isoformat())
            params.append(tag_id)

            await db.execute(
                f"UPDATE file_tags SET {', '.join(updates)} WHERE id = ?",
                tuple(params)
            )

        # Return updated tag
        row = await db.fetch_one("SELECT * FROM file_tags WHERE id = ?", (tag_id,))
        return _row_to_tag(row)

    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Tag not found: {tag_id}")
    except PrinternizerValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to update tag", tag_id=tag_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update tag")


@router.delete("/{tag_id}")
async def delete_tag(tag_id: str = PathParam(..., description="Tag ID")):
    """
    Delete a tag.

    This will also remove all file-tag assignments for this tag.
    """
    try:
        db = await get_db()

        # Verify tag exists
        existing = await db.fetch_one(
            "SELECT id FROM file_tags WHERE id = ?",
            (tag_id,)
        )
        if not existing:
            raise NotFoundError(f"Tag not found: {tag_id}")

        # Delete tag (cascade will remove assignments)
        await db.execute("DELETE FROM file_tags WHERE id = ?", (tag_id,))

        logger.info("Deleted tag", tag_id=tag_id)

        return success_response(message=f"Tag {tag_id} deleted successfully")

    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Tag not found: {tag_id}")
    except Exception as e:
        logger.error("Failed to delete tag", tag_id=tag_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete tag")


# ==================== FILE-TAG ASSIGNMENT ENDPOINTS ====================

@router.get("/file/{file_checksum}", response_model=FileTagsResponse)
async def get_file_tags(file_checksum: str = PathParam(..., description="File checksum")):
    """Get all tags assigned to a specific file."""
    try:
        db = await get_db()

        rows = await db.fetch_all(
            """
            SELECT t.* FROM file_tags t
            JOIN file_tag_assignments fta ON t.id = fta.tag_id
            WHERE fta.file_checksum = ?
            ORDER BY t.name ASC
            """,
            (file_checksum,)
        )

        tags = [_row_to_tag(row) for row in rows]

        return FileTagsResponse(file_checksum=file_checksum, tags=tags)

    except Exception as e:
        logger.error("Failed to get file tags", file_checksum=file_checksum, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve file tags")


@router.post("/file/{file_checksum}/assign")
async def assign_tags_to_file(
    file_checksum: str = PathParam(..., description="File checksum"),
    tag_ids: List[str] = Query(..., description="Tag IDs to assign")
):
    """
    Assign one or more tags to a file.

    Silently ignores tags already assigned to the file.
    """
    try:
        db = await get_db()

        # Verify file exists
        file_exists = await db.fetch_one(
            "SELECT checksum FROM library_files WHERE checksum = ?",
            (file_checksum,)
        )
        if not file_exists:
            raise NotFoundError(f"File not found: {file_checksum}")

        assigned_count = 0
        for tag_id in tag_ids:
            # Verify tag exists
            tag_exists = await db.fetch_one(
                "SELECT id FROM file_tags WHERE id = ?",
                (tag_id,)
            )
            if not tag_exists:
                logger.warning("Tag not found, skipping", tag_id=tag_id)
                continue

            # Try to insert (ignore if already exists)
            try:
                await db.execute(
                    """
                    INSERT OR IGNORE INTO file_tag_assignments (file_checksum, tag_id)
                    VALUES (?, ?)
                    """,
                    (file_checksum, tag_id)
                )
                assigned_count += 1
            except Exception:
                pass  # Duplicate, ignore

        logger.info("Assigned tags to file", file_checksum=file_checksum[:16], count=assigned_count)

        return success_response(
            message=f"Assigned {assigned_count} tag(s) to file",
            data={"file_checksum": file_checksum, "assigned_count": assigned_count}
        )

    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to assign tags", file_checksum=file_checksum, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to assign tags")


@router.post("/file/{file_checksum}/remove")
async def remove_tags_from_file(
    file_checksum: str = PathParam(..., description="File checksum"),
    tag_ids: List[str] = Query(..., description="Tag IDs to remove")
):
    """Remove one or more tags from a file."""
    try:
        db = await get_db()

        removed_count = 0
        for tag_id in tag_ids:
            result = await db.execute(
                """
                DELETE FROM file_tag_assignments
                WHERE file_checksum = ? AND tag_id = ?
                """,
                (file_checksum, tag_id)
            )
            if result:
                removed_count += 1

        logger.info("Removed tags from file", file_checksum=file_checksum[:16], count=removed_count)

        return success_response(
            message=f"Removed {removed_count} tag(s) from file",
            data={"file_checksum": file_checksum, "removed_count": removed_count}
        )

    except Exception as e:
        logger.error("Failed to remove tags", file_checksum=file_checksum, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to remove tags")


@router.get("/search/files")
async def search_files_by_tags(
    tag_ids: List[str] = Query(..., description="Tag IDs to filter by"),
    match_all: bool = Query(False, description="Require all tags (AND) vs any tag (OR)")
):
    """
    Search for files by tags.

    - match_all=False (default): Return files with ANY of the specified tags (OR)
    - match_all=True: Return files with ALL specified tags (AND)
    """
    try:
        db = await get_db()

        if match_all:
            # AND logic: files must have all tags
            placeholders = ",".join("?" * len(tag_ids))
            query = f"""
                SELECT file_checksum FROM file_tag_assignments
                WHERE tag_id IN ({placeholders})
                GROUP BY file_checksum
                HAVING COUNT(DISTINCT tag_id) = ?
            """
            params = tag_ids + [len(tag_ids)]
        else:
            # OR logic: files with any tag
            placeholders = ",".join("?" * len(tag_ids))
            query = f"""
                SELECT DISTINCT file_checksum FROM file_tag_assignments
                WHERE tag_id IN ({placeholders})
            """
            params = tag_ids

        rows = await db.fetch_all(query, tuple(params))
        checksums = [row["file_checksum"] for row in rows]

        return success_response(
            message=f"Found {len(checksums)} file(s)",
            data={"file_checksums": checksums, "total": len(checksums)}
        )

    except Exception as e:
        logger.error("Failed to search files by tags", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to search files")
