"""
File upload service for managing file uploads from users.

This service is responsible for validating, saving, and processing uploaded files,
managing upload state, and integrating with the library system.
"""
import os
import json
import hashlib
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import structlog
from fastapi import UploadFile

from src.database.database import Database
from src.database.repositories import FileRepository
from src.services.event_service import EventService
from src.models.file import File, FileStatus, FileSource
from src.utils.config import get_settings

logger = structlog.get_logger()


class FileUploadService:
    """
    Service for handling file uploads.

    This service handles:
    - File validation (type, size)
    - Duplicate file detection
    - Saving uploaded files to disk
    - Creating database records
    - Triggering thumbnail extraction
    - Triggering metadata extraction
    - Library integration
    - Event emission for upload tracking

    Events Emitted:
    - file_upload_started: When upload begins
    - file_upload_progress: During upload processing
    - file_upload_complete: When upload succeeds
    - file_upload_failed: When upload fails

    Example:
        >>> uploader = FileUploadService(database, event_service, ...)
        >>> result = await uploader.upload_files([file1, file2])
        >>> for file in result['uploaded_files']:
        ...     print(f"Uploaded: {file['filename']}")
    """

    def __init__(
        self,
        database: Database,
        event_service: EventService,
        thumbnail_service=None,
        metadata_service=None,
        library_service=None,
        usage_stats_service=None
    ):
        """
        Initialize file upload service.

        Args:
            database: Database instance for storing file records
            event_service: Event service for emitting upload events
            thumbnail_service: Optional thumbnail service for extracting thumbnails
            metadata_service: Optional metadata service for extracting metadata
            library_service: Optional library service for adding uploaded files
            usage_stats_service: Optional usage statistics service for telemetry
        """
        self.database = database
        self.file_repo = FileRepository(database._connection)
        self.event_service = event_service
        self.thumbnail_service = thumbnail_service
        self.metadata_service = metadata_service
        self.library_service = library_service
        self.usage_stats_service = usage_stats_service
        self.settings = get_settings()

    def validate_file(self, filename: str, file_size: int) -> Dict[str, Any]:
        """
        Validate uploaded file against configured constraints.

        Args:
            filename: Name of the file
            file_size: Size of the file in bytes

        Returns:
            Dict with validation result:
                - valid: bool
                - error: Optional error message
                - file_type: Detected file type
        """
        # Check if uploads are enabled
        if not self.settings.enable_upload:
            return {
                "valid": False,
                "error": "File uploads are disabled on this server",
                "file_type": None
            }

        # Extract file extension
        file_ext = Path(filename).suffix.lower()

        # Validate file extension
        allowed_extensions = self.settings.allowed_upload_extensions_list
        if file_ext not in allowed_extensions:
            return {
                "valid": False,
                "error": f"File type '{file_ext}' not allowed. Allowed types: {', '.join(allowed_extensions)}",
                "file_type": file_ext
            }

        # Validate file size
        max_size_bytes = self.settings.max_upload_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            size_mb = file_size / (1024 * 1024)
            return {
                "valid": False,
                "error": f"File size ({size_mb:.1f} MB) exceeds maximum allowed size ({self.settings.max_upload_size_mb} MB)",
                "file_type": file_ext
            }

        # All validations passed
        return {
            "valid": True,
            "error": None,
            "file_type": file_ext.lstrip('.')
        }

    async def check_duplicate(self, filename: str) -> bool:
        """
        Check if a file with the same name already exists.

        Args:
            filename: Name of the file to check

        Returns:
            True if duplicate exists, False otherwise
        """
        try:
            # Query database for existing file with same filename and upload source
            conn = self.database.get_connection()
            async with conn.execute(
                """
                SELECT id FROM files
                WHERE filename = ? AND source = 'upload'
                """,
                (filename,)
            ) as cursor:
                existing = await cursor.fetchone()
            return existing is not None
        except Exception as e:
            logger.error("Error checking for duplicate file", filename=filename, error=str(e))
            return False

    async def save_uploaded_file(self, upload_file: UploadFile, destination_dir: Path) -> Dict[str, Any]:
        """
        Save uploaded file to disk.

        Args:
            upload_file: FastAPI UploadFile object
            destination_dir: Directory to save the file

        Returns:
            Dict with save result:
                - success: bool
                - file_path: Path to saved file (if successful)
                - error: Optional error message
        """
        try:
            # Ensure destination directory exists
            destination_dir.mkdir(parents=True, exist_ok=True)

            # Generate safe filename (preserve original name)
            safe_filename = Path(upload_file.filename).name
            file_path = destination_dir / safe_filename

            # Save file
            with open(file_path, "wb") as f:
                content = await upload_file.read()
                f.write(content)

            logger.info(
                "File saved successfully",
                filename=safe_filename,
                path=str(file_path),
                size=len(content)
            )

            return {
                "success": True,
                "file_path": str(file_path),
                "file_size": len(content),
                "error": None
            }

        except Exception as e:
            logger.error(
                "Error saving uploaded file",
                filename=upload_file.filename,
                error=str(e)
            )
            return {
                "success": False,
                "file_path": None,
                "file_size": 0,
                "error": f"Failed to save file: {str(e)}"
            }

    async def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA256 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            Hexadecimal hash string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def create_file_record(
        self,
        filename: str,
        file_path: str,
        file_size: int,
        file_type: str,
        is_business: bool = False,
        notes: Optional[str] = None
    ) -> str:
        """
        Create database record for uploaded file.

        Args:
            filename: Original filename
            file_path: Local file path
            file_size: File size in bytes
            file_type: File type (extension without dot)
            is_business: Whether this is a business order
            notes: Optional notes

        Returns:
            File ID of created record
        """
        file_id = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"

        # Create file metadata
        metadata = {
            "is_business": is_business,
            "uploaded_at": datetime.now().isoformat()
        }
        if notes:
            metadata["notes"] = notes

        # Calculate file hash
        try:
            file_hash = await self.calculate_file_hash(Path(file_path))
            metadata["sha256"] = file_hash
        except Exception as e:
            logger.warning("Failed to calculate file hash", error=str(e))

        # Prepare file data for database
        file_data = {
            'id': file_id,
            'printer_id': "upload",  # Use "upload" as pseudo printer_id
            'filename': filename,
            'file_path': file_path,
            'file_size': file_size,
            'file_type': file_type,
            'status': FileStatus.DOWNLOADED.value,
            'source': FileSource.UPLOAD.value,
            'metadata': json.dumps(metadata)
        }

        # Insert into database using the create_file method
        success = await self.file_repo.create(file_data)

        if not success:
            raise Exception("Failed to create file record in database")

        logger.info(
            "File record created",
            file_id=file_id,
            filename=filename,
            size=file_size
        )

        return file_id

    async def process_file_after_upload(self, file_id: str, file_path: str) -> None:
        """
        Trigger post-upload processing (thumbnails, metadata, library).

        Args:
            file_id: ID of the uploaded file
            file_path: Path to the uploaded file
        """
        # Add to library if service available
        if self.library_service:
            try:
                await self.library_service.add_file_from_upload(file_id, file_path)
                logger.info("File added to library", file_id=file_id)
            except Exception as e:
                logger.warning(
                    "Failed to add file to library",
                    file_id=file_id,
                    error=str(e)
                )

        # Extract thumbnail if service available
        if self.thumbnail_service:
            try:
                await self.thumbnail_service.process_file_thumbnails(file_path, file_id)
                logger.info("Thumbnail extraction queued", file_id=file_id)
            except Exception as e:
                logger.warning(
                    "Failed to extract thumbnail",
                    file_id=file_id,
                    error=str(e)
                )

        # Extract metadata if service available
        if self.metadata_service:
            try:
                await self.metadata_service.extract_enhanced_metadata(file_id)
                logger.info("Metadata extraction queued", file_id=file_id)
            except Exception as e:
                logger.warning(
                    "Failed to extract metadata",
                    file_id=file_id,
                    error=str(e)
                )

    async def upload_files(
        self,
        files: List[UploadFile],
        is_business: bool = False,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload multiple files.

        ⭐ PRIMARY FILE UPLOAD METHOD - Always use this for file uploads.

        This method handles:
        - File validation (type, size)
        - Duplicate detection
        - Saving files to disk
        - Creating database records
        - Triggering thumbnail/metadata extraction
        - Event emission
        - Error handling per file

        Args:
            files: List of UploadFile objects
            is_business: Whether these are business order files
            notes: Optional notes to attach to files

        Returns:
            Dict with upload results:
                - uploaded_files: List of successfully uploaded file info
                - failed_files: List of failed uploads with error messages
                - total_count: Total number of files processed
                - success_count: Number of successful uploads
                - failure_count: Number of failed uploads
        """
        uploaded_files = []
        failed_files = []
        destination_dir = Path(self.settings.downloads_path) / "uploads"

        logger.info(
            "Starting file upload",
            file_count=len(files),
            is_business=is_business
        )

        # Emit upload started event
        await self.event_service.emit_event("file_upload_started", {
            "file_count": len(files),
            "is_business": is_business
        })

        for upload_file in files:
            try:
                filename = upload_file.filename

                # Validate file
                logger.info("Validating file", filename=filename)
                validation = self.validate_file(filename, upload_file.size)

                if not validation["valid"]:
                    logger.warning(
                        "File validation failed",
                        filename=filename,
                        error=validation["error"]
                    )
                    failed_files.append({
                        "filename": filename,
                        "error": validation["error"]
                    })
                    # Emit failure event
                    await self.event_service.emit_event("file_upload_failed", {
                        "filename": filename,
                        "error": validation["error"]
                    })
                    continue

                # Check for duplicates
                is_duplicate = await self.check_duplicate(filename)
                if is_duplicate:
                    error_msg = f"File '{filename}' already exists in library"
                    logger.warning("Duplicate file detected", filename=filename)
                    failed_files.append({
                        "filename": filename,
                        "error": error_msg
                    })
                    # Emit failure event
                    await self.event_service.emit_event("file_upload_failed", {
                        "filename": filename,
                        "error": error_msg
                    })
                    continue

                # Save file to disk
                logger.info("Saving file", filename=filename)
                save_result = await self.save_uploaded_file(upload_file, destination_dir)

                if not save_result["success"]:
                    logger.error(
                        "File save failed",
                        filename=filename,
                        error=save_result["error"]
                    )
                    failed_files.append({
                        "filename": filename,
                        "error": save_result["error"]
                    })
                    # Emit failure event
                    await self.event_service.emit_event("file_upload_failed", {
                        "filename": filename,
                        "error": save_result["error"]
                    })
                    continue

                # Create database record
                logger.info("Creating file record", filename=filename)
                file_id = await self.create_file_record(
                    filename=filename,
                    file_path=save_result["file_path"],
                    file_size=save_result["file_size"],
                    file_type=validation["file_type"],
                    is_business=is_business,
                    notes=notes
                )

                # Trigger post-processing
                await self.process_file_after_upload(file_id, save_result["file_path"])

                # Add to successful uploads
                uploaded_files.append({
                    "file_id": file_id,
                    "filename": filename,
                    "file_path": save_result["file_path"],
                    "file_size": save_result["file_size"],
                    "file_type": validation["file_type"]
                })

                # Emit success event
                await self.event_service.emit_event("file_upload_complete", {
                    "file_id": file_id,
                    "filename": filename,
                    "file_size": save_result["file_size"]
                })

                logger.info(
                    "File uploaded successfully",
                    file_id=file_id,
                    filename=filename
                )

                # Record usage statistics (privacy-safe: no filenames or personal data)
                if self.usage_stats_service:
                    await self.usage_stats_service.record_event("file_uploaded", {
                        "file_size_mb": round(save_result["file_size"] / (1024 * 1024), 2),
                        "is_business": is_business
                    })

            except Exception as e:
                logger.error(
                    "Unexpected error during file upload",
                    filename=upload_file.filename,
                    error=str(e)
                )
                failed_files.append({
                    "filename": upload_file.filename,
                    "error": f"Unexpected error: {str(e)}"
                })
                # Emit failure event
                await self.event_service.emit_event("file_upload_failed", {
                    "filename": upload_file.filename,
                    "error": str(e)
                })

        # Summary
        result = {
            "uploaded_files": uploaded_files,
            "failed_files": failed_files,
            "total_count": len(files),
            "success_count": len(uploaded_files),
            "failure_count": len(failed_files)
        }

        logger.info(
            "File upload completed",
            total=result["total_count"],
            success=result["success_count"],
            failed=result["failure_count"]
        )

        return result
