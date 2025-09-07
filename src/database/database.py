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
            async with self._connection.execute("""
                INSERT INTO printers (id, name, type, ip_address, api_key, access_code, serial_number, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                printer_data['id'],
                printer_data['name'], 
                printer_data['type'],
                printer_data.get('ip_address'),
                printer_data.get('api_key'),
                printer_data.get('access_code'),
                printer_data.get('serial_number'),
                printer_data.get('is_active', True)
            )):
                pass
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error("Failed to create printer", error=str(e))
            return False
    
    async def get_printer(self, printer_id: str) -> Optional[Dict[str, Any]]:
        """Get printer by ID."""
        try:
            async with self._connection.execute(
                "SELECT * FROM printers WHERE id = ?", (printer_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error("Failed to get printer", printer_id=printer_id, error=str(e))
            return None
    
    async def list_printers(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """List all printers."""
        try:
            query = "SELECT * FROM printers"
            params = ()
            if active_only:
                query += " WHERE is_active = 1"
            
            async with self._connection.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error("Failed to list printers", error=str(e))
            return []
    
    async def update_printer_status(self, printer_id: str, status: str, last_seen: Optional[datetime] = None) -> bool:
        """Update printer status and last seen time."""
        try:
            if last_seen is None:
                last_seen = datetime.now()
            
            async with self._connection.execute(
                "UPDATE printers SET status = ?, last_seen = ? WHERE id = ?",
                (status, last_seen.isoformat(), printer_id)
            ):
                pass
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error("Failed to update printer status", printer_id=printer_id, error=str(e))
            return False
    
    # Job CRUD Operations  
    async def create_job(self, job_data: Dict[str, Any]) -> bool:
        """Create a new job record."""
        try:
            async with self._connection.execute("""
                INSERT INTO jobs (id, printer_id, printer_type, job_name, filename, status, 
                                estimated_duration, is_business, customer_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_data['id'],
                job_data['printer_id'],
                job_data['printer_type'], 
                job_data['job_name'],
                job_data.get('filename'),
                job_data.get('status', 'pending'),
                job_data.get('estimated_duration'),
                job_data.get('is_business', False),
                job_data.get('customer_info')  # Should be JSON string
            )):
                pass
            await self._connection.commit()
            return True
        except Exception as e:
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
    
    async def list_jobs(self, printer_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List jobs with optional filtering."""
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
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY created_at DESC"
            
            async with self._connection.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error("Failed to list jobs", error=str(e))
            return []
    
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
            
            async with self._connection.execute(query, params):
                pass
            await self._connection.commit()
            return True
        except Exception as e:
            logger.error("Failed to update job", job_id=job_id, error=str(e))
            return False
    
    # File CRUD Operations
    async def create_file(self, file_data: Dict[str, Any]) -> bool:
        """Create a new file record."""
        try:
            async with self._connection.execute("""
                INSERT OR REPLACE INTO files (id, printer_id, filename, display_name, file_path, file_size, 
                                            file_type, status, source, metadata, watch_folder_path, 
                                            relative_path, modified_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_data['id'],
                file_data.get('printer_id', 'local'),  # Use 'local' for local files
                file_data['filename'],
                file_data.get('display_name'),
                file_data.get('file_path'),
                file_data.get('file_size'),
                file_data.get('file_type'),
                file_data.get('status', 'available'),
                file_data.get('source', 'printer'),
                file_data.get('metadata'),  # Should be JSON string
                file_data.get('watch_folder_path'),
                file_data.get('relative_path'),
                file_data.get('modified_time')
            )):
                pass
            await self._connection.commit()
            return True
        except Exception as e:
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
            
            async with self._connection.execute(query, params):
                pass
            await self._connection.commit()
            return True
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
            async with self._connection.execute(
                "DELETE FROM files WHERE id = ? AND source = 'local_watch'", (file_id,)
            ):
                pass
            await self._connection.commit()
            return True
        except Exception as e:
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