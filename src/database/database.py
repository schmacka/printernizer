"""
Database connection and management for Printernizer.
SQLite database with async support for job tracking and printer management.
"""
import asyncio
import aiosqlite
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog
from contextlib import asynccontextmanager
import time
import sqlite3

logger = structlog.get_logger()


class Database:
    """SQLite database manager for Printernizer."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection."""
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "printernizer.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[aiosqlite.Connection] = None
        
    async def initialize(self):
        """Initialize database and create tables."""
        logger.info("Initializing database", path=str(self.db_path))
        
        self._connection = await aiosqlite.connect(str(self.db_path))
        self._connection.row_factory = aiosqlite.Row
        
        # Create tables
        await self._create_tables()
        
        # Run migrations
        await self._run_migrations()
        
        logger.info("Database initialized successfully")
        
    async def _create_tables(self):
        """Create database tables if they don't exist."""
        async with self._connection.cursor() as cursor:
            # Jobs table - Enhanced for German business requirements
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY NOT NULL CHECK(length(id) > 0),
                    printer_id TEXT NOT NULL,
                    printer_type TEXT NOT NULL,
                    job_name TEXT NOT NULL,
                    filename TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    estimated_duration INTEGER,
                    actual_duration INTEGER,
                    progress INTEGER DEFAULT 0,
                    material_used REAL,
                    material_cost REAL,
                    power_cost REAL,
                    is_business BOOLEAN DEFAULT 0,
                    customer_info TEXT, -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Files table - Enhanced for Drucker-Dateien system
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    printer_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    display_name TEXT,
                    file_path TEXT,
                    file_size INTEGER,
                    file_type TEXT,
                    status TEXT DEFAULT 'available',
                    source TEXT DEFAULT 'printer',
                    download_progress INTEGER DEFAULT 0,
                    downloaded_at TIMESTAMP,
                    metadata TEXT, -- JSON string
                    watch_folder_path TEXT, -- Path to watch folder for local files
                    relative_path TEXT, -- Relative path within watch folder
                    modified_time TIMESTAMP, -- File modification time
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(printer_id, filename)
                )
            """)
            
            # Add indexes for better query performance
            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_source ON files(source)
            """)
            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)
            """)
            await cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_files_watch_folder ON files(watch_folder_path)
            """)

            # Ideas table for print idea management
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS ideas (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    source_type TEXT CHECK(source_type IN ('manual', 'makerworld', 'printables')),
                    source_url TEXT,
                    thumbnail_path TEXT,
                    category TEXT,
                    priority INTEGER CHECK(priority BETWEEN 1 AND 5),
                    status TEXT CHECK(status IN ('idea', 'planned', 'printing', 'completed', 'archived')) DEFAULT 'idea',
                    is_business BOOLEAN DEFAULT FALSE,
                    estimated_print_time INTEGER, -- in minutes
                    material_notes TEXT,
                    customer_info TEXT,
                    planned_date DATE,
                    completed_date DATE,
                    metadata TEXT, -- JSON string for platform-specific data
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Trending cache table for external platform models
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS trending_cache (
                    id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    thumbnail_url TEXT,
                    thumbnail_local_path TEXT,
                    downloads INTEGER,
                    likes INTEGER,
                    creator TEXT,
                    category TEXT,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    UNIQUE(platform, model_id)
                )
            """)

            # Tags table for many-to-many relationship with ideas
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS idea_tags (
                    idea_id TEXT,
                    tag TEXT,
                    FOREIGN KEY (idea_id) REFERENCES ideas (id) ON DELETE CASCADE,
                    PRIMARY KEY (idea_id, tag)
                )
            """)

            # Create indexes for ideas tables
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_ideas_status ON ideas(status)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_ideas_priority ON ideas(priority)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_ideas_is_business ON ideas(is_business)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_trending_platform ON trending_cache(platform)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_trending_expires ON trending_cache(expires_at)")

            # Printers table - Enhanced configuration
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS printers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    ip_address TEXT,
                    api_key TEXT,
                    access_code TEXT,
                    serial_number TEXT,
                    status TEXT DEFAULT 'unknown',
                    last_seen TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_printer_id ON jobs(printer_id)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_printer_id ON files(printer_id)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)")
            
        await self._connection.commit()
        logger.info("Database tables created successfully")

    # ------------------------------------------------------------------
    # Instrumentation & helper methods (Phase 1: internal use only)
    # ------------------------------------------------------------------
    async def _execute_write(self, sql: str, params: Optional[tuple] = None,
                             *, retries: int = 1, retry_delay: float = 0.05) -> bool:
        """Execute a write statement with timing + limited retry.

        Args:
            sql: SQL statement (INSERT/UPDATE/DELETE)
            params: Parameters tuple
            retries: Additional retry attempts on sqlite OperationalError
            retry_delay: Initial delay for exponential backoff
        Returns:
            True if success else False
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")
        attempt = 0
        delay = retry_delay
        while True:
            start = time.perf_counter()
            try:
                async with self._connection.execute(sql, params or ()):  # type: ignore[arg-type]
                    pass
                await self._connection.commit()
                duration_ms = (time.perf_counter() - start) * 1000
                logger.debug("db.write", sql=sql.split('\n')[0][:100], duration_ms=round(duration_ms, 2), attempt=attempt)
                return True
            except sqlite3.OperationalError as e:
                if attempt < retries:
                    logger.warning("db.write.retry", error=str(e), attempt=attempt)
                    await asyncio.sleep(delay)
                    attempt += 1
                    delay *= 2
                    continue
                logger.error("db.write.failed", error=str(e), sql=sql.split('\n')[0][:140])
                return False
            except Exception as e:  # pragma: no cover
                logger.error("db.write.exception", error=str(e))
                return False

    async def _fetch_one(self, sql: str, params: Optional[List[Any]] = None):
        if not self._connection:
            raise RuntimeError("Database not initialized")
        start = time.perf_counter()
        try:
            async with self._connection.execute(sql, params or []) as cursor:
                row = await cursor.fetchone()
            duration_ms = (time.perf_counter() - start) * 1000
            logger.debug("db.select.one", sql=sql.split('\n')[0][:100], hit=bool(row), duration_ms=round(duration_ms, 2))
            return row
        except Exception as e:
            logger.error("db.select.one.failed", error=str(e), sql=sql.split('\n')[0][:140])
            return None

    async def _fetch_all(self, sql: str, params: Optional[List[Any]] = None):
        if not self._connection:
            raise RuntimeError("Database not initialized")
        start = time.perf_counter()
        try:
            async with self._connection.execute(sql, params or []) as cursor:
                rows = await cursor.fetchall()
            duration_ms = (time.perf_counter() - start) * 1000
            logger.debug("db.select", sql=sql.split('\n')[0][:100], rows=len(rows), duration_ms=round(duration_ms, 2))
            return rows
        except Exception as e:
            logger.error("db.select.failed", error=str(e), sql=sql.split('\n')[0][:140])
            return []
        
    async def close(self):
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            logger.info("Database connection closed")
            
    def get_connection(self) -> aiosqlite.Connection:
        """Get database connection."""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        return self._connection
    
    @asynccontextmanager
    async def connection(self):
        """Get database connection as async context manager."""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        yield self._connection
        
    async def health_check(self) -> bool:
        """Check database health."""
        try:
            if not self._connection:
                return False
            # Simple query to check database is working
            async with self._connection.execute("SELECT 1") as cursor:
                await cursor.fetchone()
            return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False
    
    @asynccontextmanager
    async def transaction(self):
        """Database transaction context manager."""
        if not self._connection:
            raise RuntimeError("Database not initialized")
        async with self._connection:
            yield self._connection
    
    # Printer CRUD Operations
    async def create_printer(self, printer_data: Dict[str, Any]) -> bool:
        """Create a new printer record."""
        try:
            return await self._execute_write(
                """INSERT INTO printers (id, name, type, ip_address, api_key, access_code, serial_number, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    printer_data['id'],
                    printer_data['name'],
                    printer_data['type'],
                    printer_data.get('ip_address'),
                    printer_data.get('api_key'),
                    printer_data.get('access_code'),
                    printer_data.get('serial_number'),
                    printer_data.get('is_active', True)
                )
            )
        except Exception as e:  # pragma: no cover
            logger.error("Failed to create printer", error=str(e))
            return False
    
    async def get_printer(self, printer_id: str) -> Optional[Dict[str, Any]]:
        """Get printer by ID."""
        try:
            row = await self._fetch_one("SELECT * FROM printers WHERE id = ?", [printer_id])
            return dict(row) if row else None
        except Exception as e:  # pragma: no cover
            logger.error("Failed to get printer", printer_id=printer_id, error=str(e))
            return None
    
    async def list_printers(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """List all printers."""
        try:
            query = "SELECT * FROM printers"
            params: List[Any] = []
            if active_only:
                query += " WHERE is_active = 1"
            rows = await self._fetch_all(query, params)
            return [dict(r) for r in rows]
        except Exception as e:  # pragma: no cover
            logger.error("Failed to list printers", error=str(e))
            return []
    
    async def update_printer_status(self, printer_id: str, status: str, last_seen: Optional[datetime] = None) -> bool:
        """Update printer status and last seen time."""
        try:
            if last_seen is None:
                last_seen = datetime.now()
            return await self._execute_write(
                "UPDATE printers SET status = ?, last_seen = ? WHERE id = ?",
                (status, last_seen.isoformat(), printer_id)
            )
        except Exception as e:  # pragma: no cover
            logger.error("Failed to update printer status", printer_id=printer_id, error=str(e))
            return False
    
    # Job CRUD Operations  
    async def create_job(self, job_data: Dict[str, Any]) -> bool:
        """Create a new job record."""
        try:
            return await self._execute_write(
                """INSERT INTO jobs (id, printer_id, printer_type, job_name, filename, status,
                                estimated_duration, is_business, customer_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    job_data['id'],
                    job_data['printer_id'],
                    job_data['printer_type'],
                    job_data['job_name'],
                    job_data.get('filename'),
                    job_data.get('status', 'pending'),
                    job_data.get('estimated_duration'),
                    job_data.get('is_business', False),
                    job_data.get('customer_info')
                )
            )
        except Exception as e:  # pragma: no cover
            logger.error("Failed to create job", error=str(e))
            return False
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID."""
        try:
            async with self._connection.execute(
                "SELECT * FROM jobs WHERE id = ?", (job_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error("Failed to get job", job_id=job_id, error=str(e))
            return None
    
    async def list_jobs(self, printer_id: Optional[str] = None, status: Optional[str] = None, 
                       is_business: Optional[bool] = None, limit: Optional[int] = None, 
                       offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """List jobs with optional filtering and pagination."""
        try:
            query = "SELECT * FROM jobs"
            params = []
            conditions = []
            
            if printer_id:
                conditions.append("printer_id = ?")
                params.append(printer_id)
            if status:
                conditions.append("status = ?")
                params.append(status)
            if is_business is not None:
                conditions.append("is_business = ?")
                params.append(int(is_business))
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY created_at DESC"
            
            # Add pagination
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
                if offset is not None:
                    query += " OFFSET ?"
                    params.append(offset)
            
            async with self._connection.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error("Failed to list jobs", error=str(e))
            return []
    
    async def get_jobs_by_date_range(self, start_date: str, end_date: str, 
                                   is_business: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get jobs within a date range for reporting."""
        try:
            query = "SELECT * FROM jobs WHERE created_at BETWEEN ? AND ?"
            params = [start_date, end_date]
            
            if is_business is not None:
                query += " AND is_business = ?"
                params.append(int(is_business))
            
            query += " ORDER BY created_at DESC"
            
            async with self._connection.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error("Failed to get jobs by date range", error=str(e))
            return []
    
    async def get_job_statistics(self) -> Dict[str, Any]:
        """Get comprehensive job statistics."""
        try:
            stats = {}
            
            # Total job counts by status
            async with self._connection.execute("""
                SELECT status, COUNT(*) as count 
                FROM jobs 
                GROUP BY status
            """) as cursor:
                status_rows = await cursor.fetchall()
                for row in status_rows:
                    stats[f"{row['status']}_jobs"] = row['count']
            
            # Business vs Private job counts
            async with self._connection.execute("""
                SELECT is_business, COUNT(*) as count 
                FROM jobs 
                GROUP BY is_business
            """) as cursor:
                business_rows = await cursor.fetchall()
                for row in business_rows:
                    key = "business_jobs" if row['is_business'] else "private_jobs"
                    stats[key] = row['count']
            
            # Material and cost statistics
            async with self._connection.execute("""
                SELECT 
                    SUM(material_used) as total_material,
                    AVG(material_used) as avg_material,
                    SUM(material_cost) as total_material_cost,
                    AVG(material_cost) as avg_material_cost,
                    SUM(power_cost) as total_power_cost,
                    AVG(power_cost) as avg_power_cost,
                    SUM(actual_duration) as total_print_time,
                    AVG(actual_duration) as avg_print_time
                FROM jobs 
                WHERE status = 'completed'
            """) as cursor:
                cost_row = await cursor.fetchone()
                if cost_row:
                    stats.update({
                        'total_material_used': cost_row['total_material'] or 0,
                        'avg_material_used': cost_row['avg_material'] or 0,
                        'total_material_cost': cost_row['total_material_cost'] or 0,
                        'avg_material_cost': cost_row['avg_material_cost'] or 0,
                        'total_power_cost': cost_row['total_power_cost'] or 0,
                        'avg_power_cost': cost_row['avg_power_cost'] or 0,
                        'total_print_time': cost_row['total_print_time'] or 0,
                        'avg_print_time': cost_row['avg_print_time'] or 0
                    })
            
            # Total jobs count
            async with self._connection.execute("SELECT COUNT(*) as total FROM jobs") as cursor:
                total_row = await cursor.fetchone()
                stats['total_jobs'] = total_row['total'] if total_row else 0
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get job statistics", error=str(e))
            return {}
    
    async def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update job with provided fields."""
        try:
            # Build dynamic update query
            set_clauses = []
            params = []
            
            for field, value in updates.items():
                if field not in ['id', 'created_at']:  # Protect immutable fields
                    set_clauses.append(f"{field} = ?")
                    params.append(value)
            
            if not set_clauses:
                return True  # Nothing to update
                
            set_clauses.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(job_id)
            
            query = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE id = ?"
            
            return await self._execute_write(query, tuple(params))
        except Exception as e:
            logger.error("Failed to update job", job_id=job_id, error=str(e))
            return False
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job record from the database."""
        try:
            ok = await self._execute_write("DELETE FROM jobs WHERE id = ?", (job_id,))
            if ok:
                logger.info("Job deleted from database", job_id=job_id)
            return ok
        except Exception as e:  # pragma: no cover
            logger.error("Failed to delete job", job_id=job_id, error=str(e))
            return False
    
    # File CRUD Operations
    async def create_file(self, file_data: Dict[str, Any]) -> bool:
        """Create a new file record or update if exists (preserving thumbnails)."""
        try:
            file_id = file_data['id']

            # Check if file already exists
            async with self._connection.execute("SELECT id, has_thumbnail, thumbnail_data, thumbnail_width, thumbnail_height, thumbnail_format, thumbnail_source FROM files WHERE id = ?", (file_id,)) as cursor:
                existing = await cursor.fetchone()

            if existing:
                # File exists - update only non-thumbnail fields to preserve thumbnail data
                updates = {
                    'display_name': file_data.get('display_name'),
                    'file_size': file_data.get('file_size'),
                    'file_type': file_data.get('file_type'),
                    'modified_time': file_data.get('modified_time')
                }

                # Only update file_path and status if provided (e.g., after download)
                if file_data.get('file_path'):
                    updates['file_path'] = file_data['file_path']
                if file_data.get('status'):
                    updates['status'] = file_data['status']

                # Update metadata if provided
                if file_data.get('metadata'):
                    updates['metadata'] = file_data['metadata']

                return await self.update_file(file_id, updates)
            else:
                # New file - insert with all fields
                return await self._execute_write(
                    """INSERT INTO files (id, printer_id, filename, display_name, file_path, file_size,
                                                file_type, status, source, metadata, watch_folder_path,
                                                relative_path, modified_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        file_id,
                        file_data.get('printer_id', 'local'),
                        file_data['filename'],
                        file_data.get('display_name'),
                        file_data.get('file_path'),
                        file_data.get('file_size'),
                        file_data.get('file_type'),
                        file_data.get('status', 'available'),
                        file_data.get('source', 'printer'),
                        file_data.get('metadata'),
                        file_data.get('watch_folder_path'),
                        file_data.get('relative_path'),
                        file_data.get('modified_time')
                    )
                )
        except Exception as e:  # pragma: no cover
            logger.error("Failed to create file", error=str(e))
            return False
    
    async def list_files(self, printer_id: Optional[str] = None, status: Optional[str] = None,
                        source: Optional[str] = None) -> List[Dict[str, Any]]:
        """List files with optional filtering."""
        try:
            query = "SELECT * FROM files"
            params = []
            conditions = []

            if printer_id:
                conditions.append("printer_id = ?")
                params.append(printer_id)
            if status:
                conditions.append("status = ?")
                params.append(status)
            if source:
                conditions.append("source = ?")
                params.append(source)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY created_at DESC"

            async with self._connection.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                files = []
                for row in rows:
                    file_data = dict(row)
                    # Deserialize JSON metadata back to dict
                    if file_data.get('metadata') and isinstance(file_data['metadata'], str):
                        try:
                            file_data['metadata'] = json.loads(file_data['metadata'])
                        except (json.JSONDecodeError, TypeError):
                            # If deserialization fails, set to empty dict
                            file_data['metadata'] = {}
                    files.append(file_data)
                return files
        except Exception as e:
            logger.error("Failed to list files", error=str(e))
            return []
    
    async def update_file(self, file_id: str, updates: Dict[str, Any]) -> bool:
        """Update file with provided fields."""
        try:
            # Build dynamic update query
            set_clauses = []
            params = []

            for field, value in updates.items():
                if field not in ['id', 'printer_id', 'filename', 'created_at']:  # Protect immutable fields
                    # Handle special types that need JSON serialization
                    if field == 'metadata' and isinstance(value, dict):
                        value = json.dumps(value)

                    set_clauses.append(f"{field} = ?")
                    params.append(value)
            
            if not set_clauses:
                return True  # Nothing to update
                
            params.append(file_id)
            query = f"UPDATE files SET {', '.join(set_clauses)} WHERE id = ?"
            
            return await self._execute_write(query, tuple(params))
        except Exception as e:
            logger.error("Failed to update file", file_id=file_id, error=str(e))
            return False
    
    async def update_file_enhanced_metadata(self, file_id: str, enhanced_metadata: Dict[str, Any], 
                                           last_analyzed: datetime) -> bool:
        """
        Update file with enhanced metadata (Issue #43 - METADATA-001).
        
        This method stores comprehensive metadata extracted from 3D files including
        physical properties, print settings, material requirements, cost analysis,
        quality metrics, and compatibility information.
        """
        try:
            import json
            
            # Extract individual fields from enhanced metadata structure
            physical_props = enhanced_metadata.get('physical_properties') or {}
            print_settings = enhanced_metadata.get('print_settings') or {}
            material_req = enhanced_metadata.get('material_requirements') or {}
            cost_breakdown = enhanced_metadata.get('cost_breakdown') or {}
            quality_metrics = enhanced_metadata.get('quality_metrics') or {}
            compatibility = enhanced_metadata.get('compatibility_info') or {}
            
            # Build update query with all enhanced metadata fields
            updates = {
                # Physical properties
                'model_width': physical_props.get('width'),
                'model_depth': physical_props.get('depth'),
                'model_height': physical_props.get('height'),
                'model_volume': physical_props.get('volume'),
                'surface_area': physical_props.get('surface_area'),
                'object_count': physical_props.get('object_count', 1),
                
                # Print settings
                'nozzle_diameter': print_settings.get('nozzle_diameter'),
                'wall_count': print_settings.get('wall_count'),
                'wall_thickness': print_settings.get('wall_thickness'),
                'infill_pattern': print_settings.get('infill_pattern'),
                'first_layer_height': print_settings.get('first_layer_height'),
                
                # Material information
                'total_filament_weight': material_req.get('total_weight'),
                'filament_length': material_req.get('filament_length'),
                'filament_colors': json.dumps(material_req.get('filament_colors', [])) if material_req.get('filament_colors') else None,
                
                # Cost analysis
                'material_cost': cost_breakdown.get('material_cost'),
                'energy_cost': cost_breakdown.get('energy_cost'),
                'total_cost': cost_breakdown.get('total_cost'),
                
                # Quality metrics
                'complexity_score': quality_metrics.get('complexity_score'),
                'success_probability': quality_metrics.get('success_probability'),
                'difficulty_level': quality_metrics.get('difficulty_level'),
                
                # Compatibility
                'compatible_printers': json.dumps(compatibility.get('compatible_printers', [])) if compatibility.get('compatible_printers') else None,
                'slicer_name': compatibility.get('slicer_name'),
                'slicer_version': compatibility.get('slicer_version'),
                'profile_name': compatibility.get('profile_name'),
                
                # Metadata timestamp
                'last_analyzed': last_analyzed.isoformat() if isinstance(last_analyzed, datetime) else last_analyzed
            }
            
            # Filter out None values
            updates = {k: v for k, v in updates.items() if v is not None}
            
            # Use existing update_file method
            return await self.update_file(file_id, updates)
            
        except Exception as e:
            logger.error("Failed to update file enhanced metadata", file_id=file_id, error=str(e))
            return False
    
    async def create_local_file(self, file_data: Dict[str, Any]) -> bool:
        """Create a local file record specifically for watch folder files."""
        local_file_data = {
            **file_data,
            'printer_id': 'local',
            'source': 'local_watch',
            'status': 'local'
        }
        return await self.create_file(local_file_data)
    
    async def list_local_files(self, watch_folder_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """List local files from watch folders."""
        try:
            query = "SELECT * FROM files WHERE source = 'local_watch'"
            params = []
            
            if watch_folder_path:
                query += " AND watch_folder_path = ?"
                params.append(watch_folder_path)
            
            query += " ORDER BY modified_time DESC"
            
            async with self._connection.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error("Failed to list local files", error=str(e))
            return []
    
    async def delete_local_file(self, file_id: str) -> bool:
        """Delete a local file record."""
        try:
            return await self._execute_write("DELETE FROM files WHERE id = ? AND source = 'local_watch'", (file_id,))
        except Exception as e:  # pragma: no cover
            logger.error("Failed to delete local file", file_id=file_id, error=str(e))
            return False
    
    async def get_file_statistics(self) -> Dict[str, Any]:
        """Get file statistics by source."""
        try:
            stats = {}
            
            # Total counts
            async with self._connection.execute("SELECT COUNT(*), source FROM files GROUP BY source") as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    source = row[1] or 'unknown'
                    stats[f"{source}_count"] = row[0]
            
            # Total size by source
            async with self._connection.execute("SELECT SUM(file_size), source FROM files GROUP BY source") as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    source = row[1] or 'unknown'
                    stats[f"{source}_size"] = row[0] or 0
            
            # Status counts
            async with self._connection.execute("SELECT COUNT(*), status FROM files GROUP BY status") as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    status = row[1] or 'unknown'
                    stats[f"{status}_count"] = row[0]
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get file statistics", error=str(e))
            return {}

    # Ideas CRUD Operations
    async def create_idea(self, idea_data: Dict[str, Any]) -> bool:
        """Create a new idea record."""
        try:
            return await self._execute_write(
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
        except Exception as e:
            logger.error("Failed to create idea", error=str(e))
            return False

    async def get_idea(self, idea_id: str) -> Optional[Dict[str, Any]]:
        """Get idea by ID."""
        try:
            row = await self._fetch_one("SELECT * FROM ideas WHERE id = ?", [idea_id])
            return dict(row) if row else None
        except Exception as e:
            logger.error("Failed to get idea", idea_id=idea_id, error=str(e))
            return None

    async def list_ideas(self, status: Optional[str] = None, is_business: Optional[bool] = None,
                        category: Optional[str] = None, source_type: Optional[str] = None,
                        limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """List ideas with optional filtering and pagination."""
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

            rows = await self._fetch_all(query, params)
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error("Failed to list ideas", error=str(e))
            return []

    async def update_idea(self, idea_id: str, updates: Dict[str, Any]) -> bool:
        """Update idea with provided fields."""
        try:
            set_clauses = []
            params = []

            for field, value in updates.items():
                if field not in ['id', 'created_at']:
                    set_clauses.append(f"{field} = ?")
                    params.append(value)

            if not set_clauses:
                return True

            set_clauses.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(idea_id)

            query = f"UPDATE ideas SET {', '.join(set_clauses)} WHERE id = ?"
            return await self._execute_write(query, tuple(params))
        except Exception as e:
            logger.error("Failed to update idea", idea_id=idea_id, error=str(e))
            return False

    async def delete_idea(self, idea_id: str) -> bool:
        """Delete an idea record."""
        try:
            # First delete associated tags
            await self._execute_write("DELETE FROM idea_tags WHERE idea_id = ?", (idea_id,))
            # Then delete the idea
            return await self._execute_write("DELETE FROM ideas WHERE id = ?", (idea_id,))
        except Exception as e:
            logger.error("Failed to delete idea", idea_id=idea_id, error=str(e))
            return False

    async def update_idea_status(self, idea_id: str, status: str) -> bool:
        """Update idea status."""
        updates = {'status': status}
        if status == 'completed':
            updates['completed_date'] = datetime.now().isoformat()
        return await self.update_idea(idea_id, updates)

    # Idea Tags Operations
    async def add_idea_tags(self, idea_id: str, tags: List[str]) -> bool:
        """Add tags to an idea."""
        try:
            for tag in tags:
                await self._execute_write(
                    "INSERT OR IGNORE INTO idea_tags (idea_id, tag) VALUES (?, ?)",
                    (idea_id, tag)
                )
            return True
        except Exception as e:
            logger.error("Failed to add idea tags", idea_id=idea_id, error=str(e))
            return False

    async def remove_idea_tags(self, idea_id: str, tags: List[str]) -> bool:
        """Remove tags from an idea."""
        try:
            for tag in tags:
                await self._execute_write(
                    "DELETE FROM idea_tags WHERE idea_id = ? AND tag = ?",
                    (idea_id, tag)
                )
            return True
        except Exception as e:
            logger.error("Failed to remove idea tags", idea_id=idea_id, error=str(e))
            return False

    async def get_idea_tags(self, idea_id: str) -> List[str]:
        """Get all tags for an idea."""
        try:
            rows = await self._fetch_all(
                "SELECT tag FROM idea_tags WHERE idea_id = ?",
                [idea_id]
            )
            return [row['tag'] for row in rows]
        except Exception as e:
            logger.error("Failed to get idea tags", idea_id=idea_id, error=str(e))
            return []

    async def get_all_tags(self) -> List[Dict[str, Any]]:
        """Get all unique tags with counts."""
        try:
            rows = await self._fetch_all(
                "SELECT tag, COUNT(*) as count FROM idea_tags GROUP BY tag ORDER BY count DESC",
                []
            )
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error("Failed to get all tags", error=str(e))
            return []

    # Trending Cache Operations
    async def upsert_trending(self, trending_data: Dict[str, Any]) -> bool:
        """Insert or update trending cache entry."""
        try:
            return await self._execute_write(
                """INSERT OR REPLACE INTO trending_cache
                (id, platform, model_id, title, url, thumbnail_url, thumbnail_local_path,
                 downloads, likes, creator, category, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    trending_data['id'],
                    trending_data['platform'],
                    trending_data['model_id'],
                    trending_data['title'],
                    trending_data['url'],
                    trending_data.get('thumbnail_url'),
                    trending_data.get('thumbnail_local_path'),
                    trending_data.get('downloads'),
                    trending_data.get('likes'),
                    trending_data.get('creator'),
                    trending_data.get('category'),
                    trending_data['expires_at']
                )
            )
        except Exception as e:
            logger.error("Failed to upsert trending", error=str(e))
            return False

    async def get_trending(self, platform: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get trending items from cache."""
        try:
            query = "SELECT * FROM trending_cache WHERE expires_at > datetime('now')"
            params = []

            if platform:
                query += " AND platform = ?"
                params.append(platform)
            if category:
                query += " AND category = ?"
                params.append(category)

            query += " ORDER BY likes DESC, downloads DESC"

            rows = await self._fetch_all(query, params)
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error("Failed to get trending", error=str(e))
            return []

    async def clean_expired_trending(self) -> bool:
        """Remove expired trending cache entries."""
        try:
            return await self._execute_write(
                "DELETE FROM trending_cache WHERE expires_at < datetime('now')",
                ()
            )
        except Exception as e:
            logger.error("Failed to clean expired trending", error=str(e))
            return False

    async def get_idea_statistics(self) -> Dict[str, Any]:
        """Get idea statistics."""
        try:
            stats = {}

            # Status counts
            rows = await self._fetch_all(
                "SELECT status, COUNT(*) as count FROM ideas GROUP BY status",
                []
            )
            for row in rows:
                stats[f"{row['status']}_count"] = row['count']

            # Business vs Personal counts
            rows = await self._fetch_all(
                "SELECT is_business, COUNT(*) as count FROM ideas GROUP BY is_business",
                []
            )
            for row in rows:
                key = "business_ideas" if row['is_business'] else "personal_ideas"
                stats[key] = row['count']

            # Source type counts
            rows = await self._fetch_all(
                "SELECT source_type, COUNT(*) as count FROM ideas GROUP BY source_type",
                []
            )
            for row in rows:
                stats[f"{row['source_type']}_count"] = row['count']

            # Total ideas
            row = await self._fetch_one("SELECT COUNT(*) as total FROM ideas", [])
            stats['total_ideas'] = row['total'] if row else 0

            # Average priority
            row = await self._fetch_one("SELECT AVG(priority) as avg_priority FROM ideas WHERE priority IS NOT NULL", [])
            stats['avg_priority'] = round(row['avg_priority'], 2) if row and row['avg_priority'] else 0

            return stats
        except Exception as e:
            logger.error("Failed to get idea statistics", error=str(e))
            return {}

    # ========================================================================
    # Library Management Methods
    # ========================================================================

    async def create_library_file(self, file_data: Dict[str, Any]) -> bool:
        """Create a new library file record."""
        try:
            return await self._execute_write(
                """INSERT INTO library_files
                (id, checksum, filename, display_name, library_path, file_size, file_type,
                 sources, status, added_to_library, last_modified, search_index)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    file_data['id'],
                    file_data['checksum'],
                    file_data['filename'],
                    file_data.get('display_name'),
                    file_data['library_path'],
                    file_data['file_size'],
                    file_data['file_type'],
                    file_data['sources'],
                    file_data.get('status', 'available'),
                    file_data['added_to_library'],
                    file_data.get('last_modified'),
                    file_data.get('search_index', '')
                )
            )
        except Exception as e:
            logger.error("Failed to create library file", error=str(e))
            return False

    async def get_library_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get library file by ID."""
        row = await self._fetch_one(
            "SELECT * FROM library_files WHERE id = ?",
            [file_id]
        )
        return dict(row) if row else None

    async def get_library_file_by_checksum(self, checksum: str) -> Optional[Dict[str, Any]]:
        """Get library file by checksum."""
        row = await self._fetch_one(
            "SELECT * FROM library_files WHERE checksum = ?",
            [checksum]
        )
        return dict(row) if row else None

    async def update_library_file(self, checksum: str, updates: Dict[str, Any]) -> bool:
        """Update library file by checksum."""
        if not updates:
            return False

        # Build update query
        set_clauses = [f"{key} = ?" for key in updates.keys()]
        set_clause = ", ".join(set_clauses)

        query = f"UPDATE library_files SET {set_clause} WHERE checksum = ?"
        params = list(updates.values()) + [checksum]

        return await self._execute_write(query, tuple(params))

    async def delete_library_file(self, checksum: str) -> bool:
        """Delete library file by checksum."""
        return await self._execute_write(
            "DELETE FROM library_files WHERE checksum = ?",
            (checksum,)
        )

    async def list_library_files(self, filters: Optional[Dict[str, Any]] = None,
                                 page: int = 1, limit: int = 50) -> tuple:
        """
        List library files with filters and pagination.

        Returns:
            Tuple of (files_list, pagination_info)
        """
        try:
            filters = filters or {}

            # Build WHERE clause
            where_clauses = []
            params = []

            if filters.get('source_type'):
                where_clauses.append("sources LIKE ?")
                params.append(f'%"type": "{filters["source_type"]}"%')

            if filters.get('file_type'):
                where_clauses.append("file_type = ?")
                params.append(filters['file_type'])

            if filters.get('status'):
                where_clauses.append("status = ?")
                params.append(filters['status'])

            if filters.get('search'):
                where_clauses.append("search_index LIKE ?")
                params.append(f"%{filters['search'].lower()}%")

            if filters.get('has_thumbnail') is not None:
                where_clauses.append("has_thumbnail = ?")
                params.append(1 if filters['has_thumbnail'] else 0)

            if filters.get('has_metadata') is not None:
                where_clauses.append("last_analyzed IS NOT NULL" if filters['has_metadata'] else "last_analyzed IS NULL")

            # Build query
            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM library_files WHERE {where_clause}"
            count_row = await self._fetch_one(count_query, params)
            total_items = count_row['total'] if count_row else 0

            # Calculate pagination
            offset = (page - 1) * limit
            total_pages = (total_items + limit - 1) // limit if limit > 0 else 1

            # Get files
            order_by = "added_to_library DESC"  # Default sort
            query = f"""
                SELECT * FROM library_files
                WHERE {where_clause}
                ORDER BY {order_by}
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            rows = await self._fetch_all(query, params)
            files = [dict(row) for row in rows]

            pagination = {
                'page': page,
                'limit': limit,
                'total_items': total_items,
                'total_pages': total_pages
            }

            return files, pagination

        except Exception as e:
            logger.error("Failed to list library files", error=str(e))
            return [], {'page': page, 'limit': limit, 'total_items': 0, 'total_pages': 0}

    async def create_library_file_source(self, source_data: Dict[str, Any]) -> bool:
        """Create library file source record."""
        try:
            return await self._execute_write(
                """INSERT OR IGNORE INTO library_file_sources
                (file_checksum, source_type, source_id, source_name, original_path,
                 original_filename, discovered_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    source_data['file_checksum'],
                    source_data['source_type'],
                    source_data.get('source_id'),
                    source_data.get('source_name'),
                    source_data.get('original_path'),
                    source_data.get('original_filename'),
                    source_data['discovered_at'],
                    source_data.get('metadata')
                )
            )
        except Exception as e:
            logger.error("Failed to create library file source", error=str(e))
            return False

    async def get_library_file_sources(self, checksum: str) -> List[Dict[str, Any]]:
        """Get all sources for a library file."""
        rows = await self._fetch_all(
            "SELECT * FROM library_file_sources WHERE file_checksum = ?",
            [checksum]
        )
        return [dict(row) for row in rows]

    async def delete_library_file_sources(self, checksum: str) -> bool:
        """Delete all sources for a library file."""
        return await self._execute_write(
            "DELETE FROM library_file_sources WHERE file_checksum = ?",
            (checksum,)
        )

    async def get_library_stats(self) -> Dict[str, Any]:
        """Get library statistics."""
        try:
            row = await self._fetch_one("SELECT * FROM library_stats", [])
            return dict(row) if row else {}
        except Exception as e:
            logger.error("Failed to get library stats", error=str(e))
            return {}

    async def update_file_enhanced_metadata(self, file_id: str,
                                           enhanced_metadata: Dict[str, Any],
                                           last_analyzed: datetime) -> bool:
        """Update enhanced metadata for a file (compatibility method)."""
        # This method is for backwards compatibility with existing enhanced metadata code
        # It updates both old files table and new library_files table if they exist

        updates = {
            'last_analyzed': last_analyzed.isoformat() if isinstance(last_analyzed, datetime) else last_analyzed
        }

        # Add metadata fields
        if 'physical_properties' in enhanced_metadata and enhanced_metadata['physical_properties']:
            pp = enhanced_metadata['physical_properties']
            if 'width' in pp: updates['model_width'] = pp['width']
            if 'depth' in pp: updates['model_depth'] = pp['depth']
            if 'height' in pp: updates['model_height'] = pp['height']
            if 'volume' in pp: updates['model_volume'] = pp['volume']
            if 'surface_area' in pp: updates['surface_area'] = pp['surface_area']
            if 'object_count' in pp: updates['object_count'] = pp['object_count']

        if 'print_settings' in enhanced_metadata and enhanced_metadata['print_settings']:
            ps = enhanced_metadata['print_settings']
            if 'layer_height' in ps: updates['layer_height'] = ps['layer_height']
            if 'first_layer_height' in ps: updates['first_layer_height'] = ps['first_layer_height']
            if 'nozzle_diameter' in ps: updates['nozzle_diameter'] = ps['nozzle_diameter']
            if 'wall_count' in ps: updates['wall_count'] = ps['wall_count']
            if 'wall_thickness' in ps: updates['wall_thickness'] = ps['wall_thickness']
            if 'infill_density' in ps: updates['infill_density'] = ps['infill_density']
            if 'infill_pattern' in ps: updates['infill_pattern'] = ps['infill_pattern']
            if 'support_used' in ps: updates['support_used'] = ps['support_used']
            if 'nozzle_temperature' in ps: updates['nozzle_temperature'] = ps['nozzle_temperature']
            if 'bed_temperature' in ps: updates['bed_temperature'] = ps['bed_temperature']
            if 'print_speed' in ps: updates['print_speed'] = ps['print_speed']
            if 'total_layer_count' in ps: updates['total_layer_count'] = ps['total_layer_count']

        # Try to update in both tables
        success = False

        # Update old files table
        try:
            set_clauses = [f"{key} = ?" for key in updates.keys()]
            set_clause = ", ".join(set_clauses)
            query = f"UPDATE files SET {set_clause} WHERE id = ?"
            params = list(updates.values()) + [file_id]
            await self._execute_write(query, tuple(params))
            success = True
        except Exception as e:
            logger.debug("Could not update files table (expected if library-only)", error=str(e))

        # Update library_files table
        try:
            # Get checksum from file_id if it's a library file
            file = await self.get_library_file(file_id)
            if file:
                await self.update_library_file(file['checksum'], updates)
                success = True
        except Exception as e:
            logger.debug("Could not update library_files table", error=str(e))

        return success

    async def _run_migrations(self):
        """Run database migrations to update schema."""
        try:
            async with self._connection.cursor() as cursor:
                # Create migrations tracking table if it doesn't exist
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version TEXT NOT NULL UNIQUE,
                        description TEXT,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Check which migrations have been applied
                await cursor.execute("SELECT version FROM migrations")
                applied_migrations = {row['version'] for row in await cursor.fetchall()}

                # Migration 001: Add watch folder columns to files table
                if '001' not in applied_migrations:
                    await cursor.execute("PRAGMA table_info(files)")
                    columns = await cursor.fetchall()
                    column_names = [col['name'] for col in columns]

                    # Add watch_folder_path column if it doesn't exist
                    if 'watch_folder_path' not in column_names:
                        logger.info("Migration 001: Adding watch_folder_path column to files table")
                        await cursor.execute("ALTER TABLE files ADD COLUMN watch_folder_path TEXT")

                    # Add relative_path column if it doesn't exist
                    if 'relative_path' not in column_names:
                        logger.info("Migration 001: Adding relative_path column to files table")
                        await cursor.execute("ALTER TABLE files ADD COLUMN relative_path TEXT")

                    # Add modified_time column if it doesn't exist
                    if 'modified_time' not in column_names:
                        logger.info("Migration 001: Adding modified_time column to files table")
                        await cursor.execute("ALTER TABLE files ADD COLUMN modified_time TIMESTAMP")

                    await cursor.execute(
                        "INSERT INTO migrations (version, description) VALUES (?, ?)",
                        ('001', 'Add watch folder columns to files table')
                    )
                    logger.info("Migration 001 completed")

                # Migration 005: Fix NULL job IDs
                if '005' not in applied_migrations:
                    logger.info("Migration 005: Checking for NULL job IDs")

                    # Check if we have jobs with NULL IDs
                    await cursor.execute("SELECT COUNT(*) as count FROM jobs WHERE id IS NULL OR id = ''")
                    null_count_row = await cursor.fetchone()
                    null_count = null_count_row['count'] if null_count_row else 0

                    if null_count > 0:
                        logger.info(f"Migration 005: Found {null_count} jobs with NULL/empty IDs, fixing...")

                        # Read the migration SQL file and execute it
                        from pathlib import Path
                        migration_file = Path(__file__).parent.parent.parent / "migrations" / "005_fix_null_job_ids.sql"

                        if migration_file.exists():
                            with open(migration_file, 'r') as f:
                                migration_sql = f.read()

                            # Split by semicolons and execute each statement
                            # Skip the migration tracking insert since we'll do that separately
                            statements = [s.strip() for s in migration_sql.split(';') if s.strip() and 'INSERT INTO migrations' not in s]

                            for statement in statements:
                                if statement and not statement.startswith('--'):
                                    await cursor.execute(statement)

                            logger.info("Migration 005: Jobs table recreated with NOT NULL constraint")
                        else:
                            # Fallback: Generate UUIDs inline
                            logger.warning("Migration file not found, using inline migration")
                            await cursor.execute("""
                                UPDATE jobs
                                SET id = lower(hex(randomblob(16)))
                                WHERE id IS NULL OR id = ''
                            """)
                    else:
                        logger.info("Migration 005: No NULL job IDs found, schema already compliant")

                    await cursor.execute(
                        "INSERT INTO migrations (version, description) VALUES (?, ?)",
                        ('005', 'Fix NULL job IDs and add NOT NULL constraint')
                    )
                    logger.info("Migration 005 completed")

                await self._connection.commit()
                logger.info("All database migrations completed successfully")

        except Exception as e:
            logger.error("Failed to run database migrations", error=str(e))
            raise