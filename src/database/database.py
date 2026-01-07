"""
Database connection and management for Printernizer.
SQLite database with async support for job tracking and printer management.

DEPRECATION NOTICE:
-------------------
Many methods in this class have been superseded by the Repository pattern (Phase 1 refactoring).
The following repositories are now the preferred way to interact with the database:

- PrinterRepository (src/database/repositories/printer_repository.py)
  Replaces: create_printer, get_printer, list_printers, update_printer_status

- JobRepository (src/database/repositories/job_repository.py)
  Replaces: create_job, get_job, list_jobs, update_job, delete_job, get_jobs_by_date_range, get_job_statistics

- FileRepository (src/database/repositories/file_repository.py)
  Replaces: create_file, list_files, update_file, delete_local_file, get_file_statistics

- SnapshotRepository (src/database/repositories/snapshot_repository.py)
  Replaces: create_snapshot, get_snapshot_by_id, list_snapshots, delete_snapshot, update_snapshot_validation

- TrendingRepository (src/database/repositories/trending_repository.py)
  Replaces: upsert_trending, get_trending, clean_expired_trending

- IdeaRepository (src/database/repositories/idea_repository.py)
  Replaces: create_idea, get_idea, list_ideas, update_idea, delete_idea, update_idea_status,
           add_idea_tags, remove_idea_tags, get_idea_tags, get_all_tags

- LibraryRepository (src/database/repositories/library_repository.py)
  Replaces: create_library_file, get_library_file, list_library_files, update_library_file,
           delete_library_file, get_library_stats

The old methods are maintained for backward compatibility during the migration period.
New code should use the repository classes directly.

Example migration:
    # Old way (deprecated)
    printer = await db.get_printer(printer_id)

    # New way (preferred)
    printer_repo = PrinterRepository(db.get_connection())
    printer = await printer_repo.get(printer_id)

See docs/technical-debt/progress-tracker.md for migration status.

CONNECTION POOLING (Phase 3):
-----------------------------
The Database class now supports connection pooling for improved concurrency.

Usage examples:
    # Using pooled connections (recommended for concurrent operations)
    async with db.pooled_connection() as conn:
        async with conn.execute("SELECT * FROM jobs") as cursor:
            rows = await cursor.fetchall()

    # Or manually acquire/release
    conn = await db.acquire_connection()
    try:
        # Use connection
        pass
    finally:
        await db.release_connection(conn)

    # Legacy usage (backward compatible)
    conn = db.get_connection()
    # Use connection directly

Configuration:
    - Default pool size: 5 connections
    - Customize: Database(db_path, pool_size=10)
    - Uses WAL mode for optimal read concurrency
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
    """SQLite database manager for Printernizer with connection pooling."""

    def __init__(self, db_path: Optional[str] = None, pool_size: int = 5):
        """
        Initialize database with connection pooling.

        Args:
            db_path: Path to SQLite database file
            pool_size: Number of connections in the pool (default: 5)
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "printernizer.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Connection pooling
        self._pool_size = pool_size
        self._connection_pool: asyncio.Queue[aiosqlite.Connection] = asyncio.Queue(maxsize=pool_size)
        self._pool_semaphore = asyncio.Semaphore(pool_size)
        self._pool_initialized = False

        # Backward compatibility: maintain single connection reference for old code
        self._connection: Optional[aiosqlite.Connection] = None
        
    async def initialize(self):
        """Initialize database, connection pool, and create tables."""
        logger.info("Initializing database with connection pool", path=str(self.db_path), pool_size=self._pool_size)

        # Create main connection for backward compatibility and initial setup
        self._connection = await aiosqlite.connect(str(self.db_path))
        self._connection.row_factory = aiosqlite.Row

        # Enable foreign key constraints
        await self._connection.execute("PRAGMA foreign_keys = ON")

        # Create tables
        await self._create_tables()

        # Run migrations
        await self._run_migrations()

        # Initialize connection pool
        await self._initialize_pool()

        logger.info("Database initialized successfully", pool_size=self._pool_size)
        
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
                    has_thumbnail BOOLEAN DEFAULT 0, -- Whether file has thumbnail
                    thumbnail_data BLOB, -- Thumbnail image data
                    thumbnail_width INTEGER, -- Thumbnail width in pixels
                    thumbnail_height INTEGER, -- Thumbnail height in pixels
                    thumbnail_format TEXT, -- Thumbnail format (png, jpg, etc.)
                    thumbnail_source TEXT, -- Thumbnail source (extracted, generated, etc.)
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(printer_id, filename)
                )
            """)
            
            # Add indexes for better query performance
            # Note: idx_files_source created in migration 001 after source column is added
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

            # Library files table for unified file management with deduplication
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS library_files (
                    id TEXT PRIMARY KEY,
                    checksum TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    display_name TEXT,
                    library_path TEXT NOT NULL,
                    file_size INTEGER,
                    file_type TEXT,
                    sources TEXT, -- JSON array of sources
                    status TEXT DEFAULT 'available',
                    added_to_library TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_modified TIMESTAMP,
                    last_analyzed TIMESTAMP,
                    search_index TEXT,
                    is_duplicate BOOLEAN DEFAULT 0,
                    duplicate_of_checksum TEXT,
                    duplicate_count INTEGER DEFAULT 0,
                    has_thumbnail BOOLEAN DEFAULT 0,
                    thumbnail_data BLOB,
                    thumbnail_width INTEGER,
                    thumbnail_height INTEGER,
                    thumbnail_format TEXT,
                    thumbnail_source TEXT,
                    metadata TEXT, -- JSON metadata
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    -- Physical properties metadata
                    model_width REAL,
                    model_depth REAL,
                    model_height REAL,
                    model_volume REAL,
                    surface_area REAL,
                    object_count INTEGER,

                    -- Print settings metadata
                    layer_height REAL,
                    first_layer_height REAL,
                    nozzle_diameter REAL,
                    wall_count INTEGER,
                    wall_thickness REAL,
                    infill_density REAL,
                    infill_pattern TEXT,
                    support_used INTEGER,
                    nozzle_temperature INTEGER,
                    bed_temperature INTEGER,
                    print_speed REAL,
                    total_layer_count INTEGER,

                    -- Material requirements metadata
                    total_filament_weight REAL,
                    filament_length REAL,
                    filament_colors TEXT,
                    material_types TEXT,
                    multi_material INTEGER,

                    -- Cost analysis metadata
                    material_cost REAL,
                    energy_cost REAL,
                    total_cost REAL,

                    -- Quality metrics metadata
                    complexity_score INTEGER,
                    difficulty_level TEXT,
                    success_probability REAL,
                    overhang_percentage REAL,

                    -- Compatibility metadata
                    compatible_printers TEXT,
                    slicer_name TEXT,
                    slicer_version TEXT,
                    profile_name TEXT,
                    bed_type TEXT,

                    -- Error tracking
                    error_message TEXT
                )
            """)

            # Library file sources table for tracking multiple sources per file
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS library_file_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_checksum TEXT NOT NULL,
                    source_type TEXT NOT NULL, -- printer, watch_folder, upload
                    source_id TEXT, -- printer ID or watch folder ID
                    source_name TEXT, -- Human-readable source name
                    original_path TEXT,
                    original_filename TEXT,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT, -- JSON metadata specific to this source
                    manufacturer TEXT, -- For filtering by manufacturer
                    printer_model TEXT, -- For filtering by printer model
                    FOREIGN KEY (file_checksum) REFERENCES library_files(checksum) ON DELETE CASCADE,
                    UNIQUE(file_checksum, source_type, source_id, original_path)
                )
            """)

            # Library statistics view - auto-calculated from library_files
            # Drop old table/view if it exists (from previous versions)
            # First try to drop as VIEW (in case it was created as VIEW)
            await cursor.execute("DROP VIEW IF EXISTS library_stats")
            # Then try to drop as TABLE (in case it was created as TABLE in old versions)
            await cursor.execute("DROP TABLE IF EXISTS library_stats")
            
            # Create as VIEW for auto-updating statistics
            await cursor.execute("""
                CREATE VIEW IF NOT EXISTS library_stats AS
                SELECT
                    COUNT(*) as total_files,
                    COALESCE(SUM(file_size), 0) as total_size,
                    COUNT(CASE WHEN has_thumbnail = 1 THEN 1 END) as files_with_thumbnails,
                    COUNT(CASE WHEN last_analyzed IS NOT NULL THEN 1 END) as files_analyzed,
                    COUNT(CASE WHEN status = 'available' THEN 1 END) as available_files,
                    COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_files,
                    COUNT(CASE WHEN status = 'error' THEN 1 END) as error_files,
                    COUNT(DISTINCT file_type) as unique_file_types,
                    COALESCE(AVG(file_size), 0) as avg_file_size,
                    COALESCE(SUM(CASE WHEN material_cost IS NOT NULL THEN material_cost ELSE 0 END), 0) as total_material_cost
                FROM library_files
            """)

            # Create indexes for library tables
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_library_files_checksum ON library_files(checksum)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_library_files_status ON library_files(status)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_library_files_file_type ON library_files(file_type)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_library_files_is_duplicate ON library_files(is_duplicate)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_library_files_added ON library_files(added_to_library)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_library_sources_checksum ON library_file_sources(file_checksum)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_library_sources_type ON library_file_sources(source_type)")

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

            # Usage Statistics - Privacy-first usage tracking
            # Stores individual usage events locally for aggregation
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_events (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    metadata TEXT,
                    submitted BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Usage settings for opt-in status and installation tracking
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for usage statistics tables
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_events_type ON usage_events(event_type)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_events_timestamp ON usage_events(timestamp)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_events_submitted ON usage_events(submitted)")

            # Slicing jobs table for slicing queue management
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS slicing_jobs (
                    id TEXT PRIMARY KEY,
                    file_checksum TEXT NOT NULL,
                    slicer_id TEXT NOT NULL,
                    profile_id TEXT,
                    target_printer_id TEXT,
                    status TEXT NOT NULL DEFAULT 'queued',
                    priority INTEGER DEFAULT 0,
                    progress INTEGER DEFAULT 0,
                    output_file_path TEXT,
                    output_gcode_checksum TEXT,
                    estimated_print_time INTEGER,
                    filament_used REAL,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    auto_upload BOOLEAN DEFAULT 0,
                    auto_start BOOLEAN DEFAULT 0,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for slicing jobs
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_slicing_jobs_status ON slicing_jobs(status)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_slicing_jobs_priority ON slicing_jobs(priority)")
            await cursor.execute("CREATE INDEX IF NOT EXISTS idx_slicing_jobs_created ON slicing_jobs(created_at)")

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

    # ============================================================================
    # Public Query Methods (for routers and external use)
    # ============================================================================

    async def fetch_one(self, sql: str, params: Optional[tuple] = None):
        """
        Execute a query and return a single row.

        Args:
            sql: SQL query string
            params: Optional tuple of query parameters

        Returns:
            Single row as dict-like object, or None if no results
        """
        # Convert tuple to list for internal method
        param_list = list(params) if params else None
        return await self._fetch_one(sql, param_list)

    async def fetch_all(self, sql: str, params: Optional[tuple] = None):
        """
        Execute a query and return all rows.

        Args:
            sql: SQL query string
            params: Optional tuple of query parameters

        Returns:
            List of rows as dict-like objects
        """
        # Convert tuple to list for internal method
        param_list = list(params) if params else None
        return await self._fetch_all(sql, param_list)

    async def execute(self, sql: str, params: Optional[tuple] = None) -> bool:
        """
        Execute a write operation (INSERT, UPDATE, DELETE).

        Args:
            sql: SQL statement
            params: Optional tuple of parameters

        Returns:
            True if successful, False otherwise
        """
        # Convert tuple to list for internal method
        param_list = list(params) if params else None
        return await self._write(sql, param_list)

    # ============================================================================
    # Connection Pool Management
    # ============================================================================

    async def _initialize_pool(self):
        """Initialize the connection pool with configured number of connections."""
        if self._pool_initialized:
            logger.warning("Connection pool already initialized")
            return

        logger.info("Initializing connection pool", size=self._pool_size)

        for i in range(self._pool_size):
            conn = await aiosqlite.connect(str(self.db_path))
            conn.row_factory = aiosqlite.Row
            await conn.execute("PRAGMA foreign_keys = ON")
            # Optimize for concurrent reads
            await conn.execute("PRAGMA journal_mode = WAL")
            await conn.execute("PRAGMA synchronous = NORMAL")
            await self._connection_pool.put(conn)

        self._pool_initialized = True
        logger.info("Connection pool initialized", connections=self._pool_size)

    async def acquire_connection(self) -> aiosqlite.Connection:
        """
        Acquire a connection from the pool.

        Returns:
            aiosqlite.Connection: Database connection from pool

        Raises:
            RuntimeError: If pool not initialized
        """
        if not self._pool_initialized:
            # Fallback to main connection if pool not initialized
            logger.warning("Pool not initialized, using main connection")
            return self._connection

        # Acquire semaphore slot
        await self._pool_semaphore.acquire()

        # Get connection from pool
        conn = await self._connection_pool.get()
        logger.debug("Connection acquired from pool", pool_size=self._connection_pool.qsize())
        return conn

    async def release_connection(self, conn: aiosqlite.Connection):
        """
        Release a connection back to the pool.

        Args:
            conn: Connection to release back to pool
        """
        if not self._pool_initialized:
            # Nothing to release if pool not used
            return

        # Return connection to pool
        await self._connection_pool.put(conn)

        # Release semaphore slot
        self._pool_semaphore.release()
        logger.debug("Connection released to pool", pool_size=self._connection_pool.qsize())

    @asynccontextmanager
    async def pooled_connection(self):
        """
        Get a database connection from pool as async context manager.

        Usage:
            async with db.pooled_connection() as conn:
                async with conn.execute("SELECT * FROM jobs") as cursor:
                    rows = await cursor.fetchall()

        Yields:
            aiosqlite.Connection: Database connection from pool
        """
        conn = await self.acquire_connection()
        try:
            yield conn
        finally:
            await self.release_connection(conn)

    async def close(self):
        """Close all database connections including pool."""
        logger.info("Closing database connections")

        # Close pool connections
        if self._pool_initialized:
            closed_count = 0
            while not self._connection_pool.empty():
                try:
                    conn = await asyncio.wait_for(self._connection_pool.get(), timeout=1.0)
                    await conn.close()
                    closed_count += 1
                except asyncio.TimeoutError:
                    break
            logger.info("Closed pool connections", count=closed_count)
            self._pool_initialized = False

        # Close main connection
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
    
    # Printer CRUD Operations
    async def create_printer(self, printer_data: Dict[str, Any]) -> bool:
        """Create a new printer record."""
        try:
            return await self._execute_write(
                """INSERT INTO printers (id, name, type, ip_address, api_key, access_code, serial_number, webcam_url, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    printer_data['id'],
                    printer_data['name'],
                    printer_data['type'],
                    printer_data.get('ip_address'),
                    printer_data.get('api_key'),
                    printer_data.get('access_code'),
                    printer_data.get('serial_number'),
                    printer_data.get('webcam_url'),
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

    async def update_printer(self, printer_id: str, updates: Dict[str, Any]) -> bool:
        """Update printer fields.

        Args:
            printer_id: Unique printer identifier
            updates: Dictionary of fields to update (name, ip_address, api_key, access_code, serial_number, webcam_url, is_active)

        Returns:
            True if update was successful, False otherwise
        """
        try:
            if not updates:
                return True

            # Map of allowed fields to their database column names
            allowed_fields = {
                'name': 'name',
                'ip_address': 'ip_address',
                'api_key': 'api_key',
                'access_code': 'access_code',
                'serial_number': 'serial_number',
                'webcam_url': 'webcam_url',
                'is_active': 'is_active',
            }

            # Build SET clause dynamically
            set_clauses = []
            values = []

            for key, value in updates.items():
                if key in allowed_fields:
                    set_clauses.append(f"{allowed_fields[key]} = ?")
                    values.append(value)

            if not set_clauses:
                return True  # No valid fields to update

            values.append(printer_id)
            query = f"UPDATE printers SET {', '.join(set_clauses)} WHERE id = ?"

            return await self._execute_write(query, tuple(values))

        except Exception as e:  # pragma: no cover
            logger.error("Failed to update printer", printer_id=printer_id, error=str(e))
            return False

    # Job CRUD Operations  
    async def create_job(self, job_data: Dict[str, Any]) -> bool:
        """Create a new job record."""
        try:
            # Build dynamic INSERT query based on which fields are provided
            # This allows database DEFAULT values to be used for created_at/updated_at
            columns = ['id', 'printer_id', 'printer_type', 'job_name', 'filename', 'status',
                      'start_time', 'end_time', 'estimated_duration', 'actual_duration', 'progress',
                      'material_used', 'material_cost', 'power_cost', 'is_business', 'customer_info']
            values = [
                job_data['id'],
                job_data['printer_id'],
                job_data['printer_type'],
                job_data['job_name'],
                job_data.get('filename'),
                job_data.get('status', 'pending'),
                job_data.get('start_time'),
                job_data.get('end_time'),
                job_data.get('estimated_duration'),
                job_data.get('actual_duration'),
                job_data.get('progress', 0),
                job_data.get('material_used'),
                job_data.get('material_cost'),
                job_data.get('power_cost'),
                job_data.get('is_business', False),
                job_data.get('customer_info')
            ]
            
            # Only include created_at/updated_at if explicitly provided (not None)
            if job_data.get('created_at') is not None:
                columns.append('created_at')
                values.append(job_data['created_at'])
            if job_data.get('updated_at') is not None:
                columns.append('updated_at')
                values.append(job_data['updated_at'])
            
            placeholders = ', '.join(['?' for _ in columns])
            column_str = ', '.join(columns)
            
            return await self._execute_write(
                f"INSERT INTO jobs ({column_str}) VALUES ({placeholders})",
                tuple(values)
            )
        except sqlite3.IntegrityError as e:
            # Handle unique constraint violations gracefully
            error_msg = str(e).lower()
            if 'unique' in error_msg or 'idx_jobs_unique_print' in error_msg:
                logger.info("Duplicate job detected (UNIQUE constraint)",
                           printer_id=job_data.get('printer_id'),
                           filename=job_data.get('filename'),
                           start_time=job_data.get('start_time'),
                           error=str(e))
                # Return False to indicate the job already exists
                return False
            else:
                # Other integrity errors (e.g., foreign key violations)
                logger.error("Database integrity error creating job",
                            error=str(e),
                            job_data=job_data)
                return False
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
                 sources, status, added_to_library, last_modified, search_index,
                 is_duplicate, duplicate_of_checksum, duplicate_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
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
                    file_data.get('search_index', ''),
                    file_data.get('is_duplicate', 0),
                    file_data.get('duplicate_of_checksum'),
                    file_data.get('duplicate_count', 0)
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

            # Check if manufacturer/model filters require JOIN
            needs_join = filters.get('manufacturer') or filters.get('printer_model')

            # Build WHERE clause
            where_clauses = []
            params = []

            if filters.get('source_type'):
                where_clauses.append("lf.sources LIKE ?")
                params.append(f'%"type": "{filters["source_type"]}"%')

            if filters.get('file_type'):
                where_clauses.append("lf.file_type = ?")
                params.append(filters['file_type'])

            if filters.get('status'):
                where_clauses.append("lf.status = ?")
                params.append(filters['status'])

            if filters.get('search'):
                where_clauses.append("lf.search_index LIKE ?")
                params.append(f"%{filters['search'].lower()}%")

            if filters.get('has_thumbnail') is not None:
                where_clauses.append("lf.has_thumbnail = ?")
                params.append(1 if filters['has_thumbnail'] else 0)

            if filters.get('has_metadata') is not None:
                where_clauses.append("lf.last_analyzed IS NOT NULL" if filters['has_metadata'] else "lf.last_analyzed IS NULL")

            # New filters for manufacturer and printer_model
            if filters.get('manufacturer'):
                where_clauses.append("lfs.manufacturer = ?")
                params.append(filters['manufacturer'])

            if filters.get('printer_model'):
                where_clauses.append("lfs.printer_model = ?")
                params.append(filters['printer_model'])

            # Filter for duplicates
            if filters.get('show_duplicates') is False:
                where_clauses.append("lf.is_duplicate = 0")

            if filters.get('only_duplicates') is True:
                where_clauses.append("lf.is_duplicate = 1")

            # Build query based on whether JOIN is needed
            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

            if needs_join:
                # Query with JOIN to library_file_sources
                count_query = f"""
                    SELECT COUNT(DISTINCT lf.checksum) as total
                    FROM library_files lf
                    INNER JOIN library_file_sources lfs ON lf.checksum = lfs.file_checksum
                    WHERE {where_clause}
                """
                count_params = params.copy()
            else:
                # Simple query without JOIN
                count_query = f"SELECT COUNT(*) as total FROM library_files lf WHERE {where_clause}"
                count_params = params.copy()

            count_row = await self._fetch_one(count_query, count_params)
            total_items = count_row['total'] if count_row else 0

            # Calculate pagination
            offset = (page - 1) * limit
            total_pages = (total_items + limit - 1) // limit if limit > 0 else 1

            # Build ORDER BY clause
            sort_by = filters.get('sort_by', 'created_at')
            sort_order = filters.get('sort_order', 'desc').upper()

            # Map frontend field names to database columns
            sort_field_map = {
                'created_at': 'lf.added_to_library',
                'filename': 'lf.filename',
                'file_size': 'lf.file_size',
                'last_modified': 'lf.last_modified'
            }

            # Get the database column name (default to added_to_library if invalid)
            db_field = sort_field_map.get(sort_by, 'lf.added_to_library')

            # Validate sort order
            if sort_order not in ['ASC', 'DESC']:
                sort_order = 'DESC'

            order_by = f"{db_field} {sort_order}"

            if needs_join:
                # Query with JOIN (distinct to avoid duplicates)
                query = f"""
                    SELECT DISTINCT lf.* FROM library_files lf
                    INNER JOIN library_file_sources lfs ON lf.checksum = lfs.file_checksum
                    WHERE {where_clause}
                    ORDER BY {order_by}
                    LIMIT ? OFFSET ?
                """
            else:
                # Simple query without JOIN
                query = f"""
                    SELECT lf.* FROM library_files lf
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
                'total_pages': total_pages,
                'page_size': limit,
                'current_page': page,
                'has_previous': page > 1,
                'has_next': page < total_pages
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
                 original_filename, discovered_at, metadata, manufacturer, printer_model)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    source_data['file_checksum'],
                    source_data['source_type'],
                    source_data.get('source_id'),
                    source_data.get('source_name'),
                    source_data.get('original_path'),
                    source_data.get('original_filename'),
                    source_data['discovered_at'],
                    source_data.get('metadata'),
                    source_data.get('manufacturer'),  # NEW
                    source_data.get('printer_model')   # NEW
                )
            )
        except Exception as e:
            logger.error("Failed to create library file source", error=str(e))
            return False


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

    async def _run_sql_migrations(self, cursor, applied_migrations: set):
        """
        Run SQL migration files from migrations/ directory.

        This method scans the migrations directory for .sql files and executes them in order.
        It handles errors gracefully (e.g., if a column already exists) and tracks which
        migrations have been applied.

        Args:
            cursor: Database cursor
            applied_migrations: Set of already applied migration versions
        """
        try:
            from pathlib import Path
            import re

            # Get migrations directory
            migrations_dir = Path(__file__).parent.parent.parent / "migrations"

            if not migrations_dir.exists():
                logger.debug("Migrations directory not found, skipping SQL migrations")
                return

            # Get all SQL migration files
            migration_files = sorted(migrations_dir.glob("[0-9][0-9][0-9]_*.sql"))

            for migration_file in migration_files:
                # Extract version number from filename (e.g., "001" from "001_add_column.sql")
                match = re.match(r'^(\d{3})_', migration_file.name)
                if not match:
                    continue

                version = match.group(1)

                # Use SQL- prefix to avoid conflicts with Python migrations
                sql_version = f"SQL-{version}"

                # Skip if already applied
                if sql_version in applied_migrations:
                    continue

                logger.info(f"Running SQL migration {version}: {migration_file.name}")

                try:
                    # Read migration file
                    with open(migration_file, 'r', encoding='utf-8') as f:
                        migration_sql = f.read()

                    # Smart SQL statement parser that handles:
                    # - Comments (-- and /* */)
                    # - Multi-line statements
                    # - CREATE TRIGGER blocks with BEGIN/END
                    # - CREATE VIEW statements
                    # - Nested parentheses
                    
                    sql_statements = []
                    current_statement = []
                    in_trigger_block = False
                    paren_depth = 0
                    
                    lines = migration_sql.split('\n')
                    for line in lines:
                        # Remove inline comments
                        if '--' in line:
                            line = line[:line.index('--')]
                        
                        line = line.strip()
                        if not line:
                            continue
                        
                        current_statement.append(line)
                        line_upper = line.upper()
                        
                        # Track if we're in a CREATE TRIGGER block (has BEGIN/END)
                        if 'CREATE TRIGGER' in line_upper:
                            in_trigger_block = True
                        
                        # Track parentheses depth for nested expressions (e.g., in CREATE VIEW)
                        paren_depth += line.count('(') - line.count(')')
                        
                        # Check for END keyword in trigger blocks
                        # In triggers, END; marks the end of the block, but it's not the end
                        # if we're still in nested parentheses
                        if in_trigger_block and 'END' in line_upper and line.endswith(';'):
                            # This is END; - marks end of trigger
                            in_trigger_block = False
                        
                        # Check if statement is complete
                        # A statement is complete when:
                        # 1. Line ends with semicolon
                        # 2. We're not in a trigger block
                        # 3. All parentheses are balanced
                        if line.endswith(';') and not in_trigger_block and paren_depth == 0:
                            # Complete statement found
                            stmt = ' '.join(current_statement)
                            if stmt.strip():
                                sql_statements.append(stmt.strip())
                            current_statement = []
                    
                    # Add any remaining statement
                    if current_statement:
                        stmt = ' '.join(current_statement)
                        if stmt.strip():
                            sql_statements.append(stmt.strip())

                    # Execute each statement
                    for statement in sql_statements:
                        # Skip migration tracking inserts (we'll add our own)
                        if 'INSERT INTO schema_migrations' in statement or 'INSERT INTO migrations' in statement:
                            continue
                        
                        # Skip transaction control statements (we manage transactions ourselves)
                        statement_upper = statement.upper().strip()
                        if statement_upper in ('BEGIN TRANSACTION;', 'BEGIN;', 'COMMIT;', 'ROLLBACK;'):
                            logger.debug(f"Skipping transaction control statement: {statement_upper}")
                            continue

                        try:
                            await cursor.execute(statement)
                        except sqlite3.OperationalError as e:
                            error_msg = str(e).lower()
                            # Ignore "duplicate column" and "already exists" errors
                            if 'duplicate column' in error_msg or 'already exists' in error_msg:
                                logger.debug(f"Skipping statement (already applied): {e}")
                                continue
                            # Ignore "no such table: configuration" errors (table may not exist yet)
                            elif 'no such table' in error_msg:
                                logger.debug(f"Skipping statement (table not found): {e}")
                                continue
                            else:
                                raise

                    # Mark migration as completed (with SQL- prefix)
                    await cursor.execute(
                        "INSERT INTO migrations (version, description) VALUES (?, ?)",
                        (sql_version, f"SQL migration: {migration_file.name}")
                    )

                    logger.info(f"Migration {version} completed successfully")

                except Exception as e:
                    logger.error(f"Failed to run migration {version}", error=str(e), migration_file=str(migration_file))
                    # Don't mark as completed if it failed
                    # Continue with other migrations

        except Exception as e:
            logger.error("Failed to run SQL migrations", error=str(e))

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

                # Run SQL migration files from migrations/ directory
                await self._run_sql_migrations(cursor, applied_migrations)

                # CRITICAL: Always check for source column (safety check for broken migrations)
                # This ensures databases from failed/partial migrations get fixed
                await cursor.execute("PRAGMA table_info(files)")
                columns = await cursor.fetchall()
                column_names = [col['name'] for col in columns] if columns else []

                if 'source' not in column_names:
                    logger.warning("CRITICAL: 'source' column missing from files table, adding it now")
                    try:
                        await cursor.execute("ALTER TABLE files ADD COLUMN source TEXT DEFAULT 'printer'")
                        logger.info("Successfully added missing 'source' column to files table")
                    except sqlite3.OperationalError as e:
                        if 'duplicate column' not in str(e).lower():
                            raise

                # Migration 001: Add watch folder columns to files table
                if '001' not in applied_migrations:
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

                    # Create index on source column
                    logger.info("Migration 001: Creating index on source column")
                    await cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_source ON files(source)")

                    await cursor.execute(
                        "INSERT INTO migrations (version, description) VALUES (?, ?)",
                        ('001', 'Add watch folder columns and source to files table')
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

                # Migration 006: Add FTS5 search tables and search history
                if '006' not in applied_migrations:
                    logger.info("Migration 006: Adding FTS5 search tables and search history")

                    # Create FTS5 virtual table for files full-text search
                    await cursor.execute("""
                        CREATE VIRTUAL TABLE IF NOT EXISTS fts_files USING fts5(
                            file_id UNINDEXED,
                            filename,
                            display_name,
                            file_type,
                            metadata,
                            tokenize='porter unicode61'
                        )
                    """)

                    # Create FTS5 virtual table for ideas full-text search
                    await cursor.execute("""
                        CREATE VIRTUAL TABLE IF NOT EXISTS fts_ideas USING fts5(
                            idea_id UNINDEXED,
                            title,
                            description,
                            tags,
                            category,
                            tokenize='porter unicode61'
                        )
                    """)

                    # Create search history table
                    await cursor.execute("""
                        CREATE TABLE IF NOT EXISTS search_history (
                            id TEXT PRIMARY KEY,
                            query TEXT NOT NULL,
                            filters TEXT,
                            results_count INTEGER DEFAULT 0,
                            sources TEXT,
                            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            user_context TEXT
                        )
                    """)

                    # Create search analytics table for tracking clicks
                    await cursor.execute("""
                        CREATE TABLE IF NOT EXISTS search_analytics (
                            id TEXT PRIMARY KEY,
                            query TEXT NOT NULL,
                            result_id TEXT NOT NULL,
                            result_source TEXT NOT NULL,
                            clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            position INTEGER
                        )
                    """)

                    # Add index for search history queries
                    await cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_search_history_query
                        ON search_history(query)
                    """)

                    # Add index for search history timestamp
                    await cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_search_history_searched_at
                        ON search_history(searched_at DESC)
                    """)

                    # Populate FTS tables with existing data
                    logger.info("Migration 006: Populating FTS tables with existing data")

                    # Populate fts_files from files table
                    await cursor.execute("""
                        INSERT INTO fts_files(file_id, filename, display_name, file_type, metadata)
                        SELECT id, filename, display_name, file_type, metadata
                        FROM files
                        WHERE id IS NOT NULL
                    """)

                    # Populate fts_ideas from ideas table
                    await cursor.execute("""
                        INSERT INTO fts_ideas(idea_id, title, description, category)
                        SELECT id, title, description, category
                        FROM ideas
                        WHERE id IS NOT NULL
                    """)

                    await cursor.execute(
                        "INSERT INTO migrations (version, description) VALUES (?, ?)",
                        ('006', 'Add FTS5 search tables and search history')
                    )
                    logger.info("Migration 006 completed")

                # Migration 007: Add thumbnail columns to files table
                if '007' not in applied_migrations:
                    logger.info("Migration 007: Adding thumbnail columns to files table")

                    # Refresh column list
                    await cursor.execute("PRAGMA table_info(files)")
                    columns = await cursor.fetchall()
                    column_names = [col['name'] for col in columns] if columns else []

                    # Add has_thumbnail column if it doesn't exist
                    if 'has_thumbnail' not in column_names:
                        logger.info("Migration 007: Adding has_thumbnail column to files table")
                        await cursor.execute("ALTER TABLE files ADD COLUMN has_thumbnail BOOLEAN DEFAULT 0")

                    # Add thumbnail_data column if it doesn't exist
                    if 'thumbnail_data' not in column_names:
                        logger.info("Migration 007: Adding thumbnail_data column to files table")
                        await cursor.execute("ALTER TABLE files ADD COLUMN thumbnail_data BLOB")

                    # Add thumbnail_width column if it doesn't exist
                    if 'thumbnail_width' not in column_names:
                        logger.info("Migration 007: Adding thumbnail_width column to files table")
                        await cursor.execute("ALTER TABLE files ADD COLUMN thumbnail_width INTEGER")

                    # Add thumbnail_height column if it doesn't exist
                    if 'thumbnail_height' not in column_names:
                        logger.info("Migration 007: Adding thumbnail_height column to files table")
                        await cursor.execute("ALTER TABLE files ADD COLUMN thumbnail_height INTEGER")

                    # Add thumbnail_format column if it doesn't exist
                    if 'thumbnail_format' not in column_names:
                        logger.info("Migration 007: Adding thumbnail_format column to files table")
                        await cursor.execute("ALTER TABLE files ADD COLUMN thumbnail_format TEXT")

                    # Add thumbnail_source column if it doesn't exist
                    if 'thumbnail_source' not in column_names:
                        logger.info("Migration 007: Adding thumbnail_source column to files table")
                        await cursor.execute("ALTER TABLE files ADD COLUMN thumbnail_source TEXT")

                    await cursor.execute(
                        "INSERT INTO migrations (version, description) VALUES (?, ?)",
                        ('007', 'Add thumbnail columns to files table')
                    )
                    logger.info("Migration 007 completed")

                # Migration 008: Add webcam_url column to printers table
                if '008' not in applied_migrations:
                    logger.info("Migration 008: Adding webcam_url column to printers table")

                    # Check current columns
                    await cursor.execute("PRAGMA table_info(printers)")
                    columns = await cursor.fetchall()
                    column_names = [col['name'] for col in columns] if columns else []

                    # Add webcam_url column if it doesn't exist
                    if 'webcam_url' not in column_names:
                        logger.info("Migration 008: Adding webcam_url column")
                        await cursor.execute("ALTER TABLE printers ADD COLUMN webcam_url TEXT")

                    await cursor.execute(
                        "INSERT INTO migrations (version, description) VALUES (?, ?)",
                        ('008', 'Add webcam_url column to printers table')
                    )
                    logger.info("Migration 008 completed")

                await self._connection.commit()
                logger.info("All database migrations completed successfully")

        except Exception as e:
            logger.error("Failed to run database migrations", error=str(e))
            raise

    # Search-related methods
    async def search_files_fts(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Full-text search on files using FTS5.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of file IDs that match the search query
        """
        try:
            sql = """
                SELECT file_id, rank
                FROM fts_files
                WHERE fts_files MATCH ?
                ORDER BY rank
                LIMIT ?
            """
            rows = await self._fetch_all(sql, [query, limit])
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error("FTS search failed for files", error=str(e), query=query)
            return []

    async def search_ideas_fts(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Full-text search on ideas using FTS5.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of idea IDs that match the search query
        """
        try:
            sql = """
                SELECT idea_id, rank
                FROM fts_ideas
                WHERE fts_ideas MATCH ?
                ORDER BY rank
                LIMIT ?
            """
            rows = await self._fetch_all(sql, [query, limit])
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error("FTS search failed for ideas", error=str(e), query=query)
            return []

    async def update_file_fts(self, file_id: str, file_data: Dict[str, Any]) -> bool:
        """Update FTS index for a file."""
        try:
            # Delete existing entry
            await self._execute_write(
                "DELETE FROM fts_files WHERE file_id = ?",
                (file_id,)
            )
            # Insert updated entry
            metadata_str = file_data.get('metadata', '')
            if isinstance(metadata_str, dict):
                metadata_str = json.dumps(metadata_str)

            await self._execute_write(
                """INSERT INTO fts_files(file_id, filename, display_name, file_type, metadata)
                   VALUES (?, ?, ?, ?, ?)""",
                (file_id, file_data.get('filename', ''), file_data.get('display_name', ''),
                 file_data.get('file_type', ''), metadata_str)
            )
            return True
        except Exception as e:
            logger.error("Failed to update file FTS index", error=str(e), file_id=file_id)
            return False

    async def update_idea_fts(self, idea_id: str, idea_data: Dict[str, Any]) -> bool:
        """Update FTS index for an idea."""
        try:
            # Delete existing entry
            await self._execute_write(
                "DELETE FROM fts_ideas WHERE idea_id = ?",
                (idea_id,)
            )
            # Insert updated entry
            tags_str = ', '.join(idea_data.get('tags', []))
            await self._execute_write(
                """INSERT INTO fts_ideas(idea_id, title, description, tags, category)
                   VALUES (?, ?, ?, ?, ?)""",
                (idea_id, idea_data.get('title', ''), idea_data.get('description', ''),
                 tags_str, idea_data.get('category', ''))
            )
            return True
        except Exception as e:
            logger.error("Failed to update idea FTS index", error=str(e), idea_id=idea_id)
            return False

    async def delete_file_fts(self, file_id: str) -> bool:
        """Delete file from FTS index."""
        try:
            return await self._execute_write(
                "DELETE FROM fts_files WHERE file_id = ?",
                (file_id,)
            )
        except Exception as e:
            logger.error("Failed to delete file from FTS index", error=str(e), file_id=file_id)
            return False

    async def delete_idea_fts(self, idea_id: str) -> bool:
        """Delete idea from FTS index."""
        try:
            return await self._execute_write(
                "DELETE FROM fts_ideas WHERE idea_id = ?",
                (idea_id,)
            )
        except Exception as e:
            logger.error("Failed to delete idea from FTS index", error=str(e), idea_id=idea_id)
            return False

    async def add_search_history(self, history_data: Dict[str, Any]) -> bool:
        """Add entry to search history."""
        try:
            filters_json = json.dumps(history_data.get('filters')) if history_data.get('filters') else None
            sources_json = json.dumps(history_data.get('sources')) if history_data.get('sources') else None

            return await self._execute_write(
                """INSERT INTO search_history (id, query, filters, results_count, sources, searched_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (history_data['id'], history_data['query'], filters_json,
                 history_data.get('results_count', 0), sources_json,
                 history_data.get('searched_at', datetime.now().isoformat()))
            )
        except Exception as e:
            logger.error("Failed to add search history", error=str(e))
            return False

    async def get_search_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent search history."""
        try:
            sql = """
                SELECT id, query, filters, results_count, sources, searched_at
                FROM search_history
                ORDER BY searched_at DESC
                LIMIT ?
            """
            rows = await self._fetch_all(sql, [limit])
            results = []
            for row in rows:
                entry = dict(row)
                # Parse JSON fields
                if entry.get('filters'):
                    try:
                        entry['filters'] = json.loads(entry['filters'])
                    except (json.JSONDecodeError, TypeError):
                        entry['filters'] = None
                if entry.get('sources'):
                    try:
                        entry['sources'] = json.loads(entry['sources'])
                    except (json.JSONDecodeError, TypeError):
                        entry['sources'] = []
                results.append(entry)
            return results
        except Exception as e:
            logger.error("Failed to get search history", error=str(e))
            return []

    async def delete_search_history(self, search_id: str) -> bool:
        """Delete a search history entry."""
        try:
            return await self._execute_write(
                "DELETE FROM search_history WHERE id = ?",
                (search_id,)
            )
        except Exception as e:
            logger.error("Failed to delete search history", error=str(e), search_id=search_id)
            return False

    async def add_search_analytics(self, analytics_data: Dict[str, Any]) -> bool:
        """Track search result click for analytics."""
        try:
            return await self._execute_write(
                """INSERT INTO search_analytics (id, query, result_id, result_source, clicked_at, position)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (analytics_data['id'], analytics_data['query'], analytics_data['result_id'],
                 analytics_data['result_source'], analytics_data.get('clicked_at', datetime.now().isoformat()),
                 analytics_data.get('position'))
            )
        except Exception as e:
            logger.error("Failed to add search analytics", error=str(e))
            return False

    # ==========================================
    # Snapshot Methods
    # ==========================================

    async def create_snapshot(self, snapshot_data: Dict[str, Any]) -> Optional[int]:
        """Create a new snapshot record.

        Args:
            snapshot_data: Dictionary containing snapshot information

        Returns:
            Snapshot ID if successful, None otherwise
        """
        try:
            metadata_json = json.dumps(snapshot_data.get('metadata')) if snapshot_data.get('metadata') else None

            cursor = await self._connection.execute(
                """INSERT INTO snapshots (
                    job_id, printer_id, filename, original_filename,
                    file_size, content_type, storage_path,
                    captured_at, capture_trigger, width, height,
                    is_valid, notes, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    snapshot_data.get('job_id'),
                    snapshot_data['printer_id'],
                    snapshot_data['filename'],
                    snapshot_data.get('original_filename'),
                    snapshot_data['file_size'],
                    snapshot_data.get('content_type', 'image/jpeg'),
                    snapshot_data['storage_path'],
                    snapshot_data.get('captured_at', datetime.now().isoformat()),
                    snapshot_data.get('capture_trigger', 'manual'),
                    snapshot_data.get('width'),
                    snapshot_data.get('height'),
                    snapshot_data.get('is_valid', True),
                    snapshot_data.get('notes'),
                    metadata_json
                )
            )
            await self._connection.commit()

            logger.info("Snapshot created", snapshot_id=cursor.lastrowid, filename=snapshot_data['filename'])
            return cursor.lastrowid

        except Exception as e:
            logger.error("Failed to create snapshot", error=str(e), snapshot_data=snapshot_data)
            return None

    async def get_snapshot_by_id(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        """Get snapshot by ID with context information.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Snapshot dictionary with context data, or None if not found
        """
        try:
            sql = """
                SELECT * FROM v_snapshots_with_context
                WHERE id = ?
            """
            row = await self._fetch_one(sql, [snapshot_id])

            if row:
                snapshot = dict(row)
                # Parse JSON metadata
                if snapshot.get('metadata'):
                    try:
                        snapshot['metadata'] = json.loads(snapshot['metadata'])
                    except (json.JSONDecodeError, TypeError):
                        snapshot['metadata'] = None
                return snapshot

            return None

        except Exception as e:
            logger.error("Failed to get snapshot", error=str(e), snapshot_id=snapshot_id)
            return None

    async def list_snapshots(
        self,
        printer_id: Optional[str] = None,
        job_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List snapshots with optional filters.

        Args:
            printer_id: Filter by printer ID
            job_id: Filter by job ID
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of snapshot dictionaries with context data
        """
        try:
            conditions = []
            params = []

            if printer_id:
                conditions.append("printer_id = ?")
                params.append(printer_id)

            if job_id:
                conditions.append("job_id = ?")
                params.append(job_id)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            sql = f"""
                SELECT * FROM v_snapshots_with_context
                {where_clause}
                ORDER BY captured_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])

            rows = await self._fetch_all(sql, params)

            snapshots = []
            for row in rows:
                snapshot = dict(row)
                # Parse JSON metadata
                if snapshot.get('metadata'):
                    try:
                        snapshot['metadata'] = json.loads(snapshot['metadata'])
                    except (json.JSONDecodeError, TypeError):
                        snapshot['metadata'] = None
                snapshots.append(snapshot)

            return snapshots

        except Exception as e:
            logger.error("Failed to list snapshots", error=str(e), printer_id=printer_id, job_id=job_id)
            return []

    async def delete_snapshot(self, snapshot_id: int) -> bool:
        """Delete a snapshot record.

        Args:
            snapshot_id: Snapshot ID to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            return await self._execute_write(
                "DELETE FROM snapshots WHERE id = ?",
                (snapshot_id,)
            )
        except Exception as e:
            logger.error("Failed to delete snapshot", error=str(e), snapshot_id=snapshot_id)
            return False

    async def update_snapshot_validation(
        self,
        snapshot_id: int,
        is_valid: bool,
        validation_error: Optional[str] = None
    ) -> bool:
        """Update snapshot validation status.

        Args:
            snapshot_id: Snapshot ID
            is_valid: Whether snapshot is valid
            validation_error: Error message if invalid

        Returns:
            True if updated, False otherwise
        """
        try:
            return await self._execute_write(
                """UPDATE snapshots
                   SET is_valid = ?, validation_error = ?, last_validated_at = ?
                   WHERE id = ?""",
                (is_valid, validation_error, datetime.now().isoformat(), snapshot_id)
            )
        except Exception as e:
            logger.error("Failed to update snapshot validation", error=str(e), snapshot_id=snapshot_id)
            return False