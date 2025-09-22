"""
Database connection and management for Printernizer.
SQLite database with async support for job tracking and printer management.
"""
import asyncio
import aiosqlite
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
                    id TEXT PRIMARY KEY,
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
        """Create a new file record."""
        try:
            return await self._execute_write(
                """INSERT OR REPLACE INTO files (id, printer_id, filename, display_name, file_path, file_size,
                                            file_type, status, source, metadata, watch_folder_path,
                                            relative_path, modified_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    file_data['id'],
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
                return [dict(row) for row in rows]
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

    async def _run_migrations(self):
        """Run database migrations to update schema."""
        try:
            async with self._connection.cursor() as cursor:
                # Check if watch_folder_path column exists in files table
                await cursor.execute("PRAGMA table_info(files)")
                columns = await cursor.fetchall()
                column_names = [col['name'] for col in columns]
                
                # Add watch_folder_path column if it doesn't exist
                if 'watch_folder_path' not in column_names:
                    logger.info("Adding watch_folder_path column to files table")
                    await cursor.execute("ALTER TABLE files ADD COLUMN watch_folder_path TEXT")
                
                # Add relative_path column if it doesn't exist
                if 'relative_path' not in column_names:
                    logger.info("Adding relative_path column to files table")
                    await cursor.execute("ALTER TABLE files ADD COLUMN relative_path TEXT")
                
                # Add modified_time column if it doesn't exist  
                if 'modified_time' not in column_names:
                    logger.info("Adding modified_time column to files table")
                    await cursor.execute("ALTER TABLE files ADD COLUMN modified_time TIMESTAMP")
                
                await self._connection.commit()
                logger.info("Database migrations completed successfully")
                
        except Exception as e:
            logger.error("Failed to run database migrations", error=str(e))
            raise