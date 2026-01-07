"""
Database migration service for Printernizer.
Handles schema migrations and data migrations on application startup.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any
import structlog

from src.database.database import Database

logger = structlog.get_logger()


class MigrationService:
    """Database migration service."""
    
    def __init__(self, database: Database = None):
        """Initialize migration service."""
        self.database = database
        self.migrations_path = Path(__file__).parent.parent.parent / "migrations"
        self.migrations_path.mkdir(exist_ok=True)
    
    async def run_migrations(self) -> None:
        """Run all pending database migrations."""
        try:
            if not self.database:
                logger.warning("No database provided to migration service, skipping migrations")
                return
                
            logger.info("Starting database migrations")
            
            # Ensure migrations table exists
            await self._ensure_migrations_table()
            
            # Get completed migrations
            completed = await self._get_completed_migrations()
            
            # Get available migration files
            migration_files = self._get_migration_files()
            
            # Run pending migrations
            pending_count = 0
            for migration_file in migration_files:
                migration_name = migration_file.stem
                
                if migration_name not in completed:
                    await self._run_migration_file(migration_file, migration_name)
                    pending_count += 1
            
            logger.info("Database migrations completed", 
                       total_migrations=len(migration_files),
                       pending_applied=pending_count)
                       
        except Exception as e:
            logger.error("Failed to run database migrations", error=str(e))
            raise
    
    async def _ensure_migrations_table(self) -> None:
        """Ensure migrations tracking table exists."""
        try:
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            conn = self.database.get_connection()
            async with conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    migration_name TEXT PRIMARY KEY NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """):
                pass
            
            await conn.commit()
                
        except Exception as e:
            logger.error("Failed to create migrations table", error=str(e))
            raise
    
    async def _get_completed_migrations(self) -> set:
        """Get set of completed migration names."""
        try:
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            conn = self.database.get_connection()
            
            # Check if migrations table exists first
            try:
                async with conn.execute("SELECT migration_name FROM schema_migrations") as cursor:
                    rows = await cursor.fetchall()
                    return {row[0] for row in rows}
            except sqlite3.OperationalError:
                # Table doesn't exist yet
                return set()
                
        except Exception as e:
            logger.error("Failed to get completed migrations", error=str(e))
            raise
    
    def _get_migration_files(self) -> List[Path]:
        """Get sorted list of migration files."""
        try:
            migration_files = list(self.migrations_path.glob("*.sql"))
            migration_files.sort()  # Sort by filename
            
            logger.debug("Found migration files", 
                        count=len(migration_files),
                        files=[f.name for f in migration_files])
            
            return migration_files
            
        except Exception as e:
            logger.error("Failed to get migration files", error=str(e))
            raise
    
    async def _run_migration_file(self, migration_file: Path, migration_name: str) -> None:
        """Run a single migration file."""
        try:
            if not self.database:
                raise RuntimeError("Database not initialized")

            logger.info("Running migration", migration_name=migration_name)

            # Read migration SQL
            sql_content = migration_file.read_text(encoding='utf-8')

            # Execute migration
            conn = self.database.get_connection()

            # Parse and execute statements individually to handle errors gracefully
            # (Similar to database.py approach for duplicate column tolerance)
            statements = self._parse_sql_statements(sql_content)

            for statement in statements:
                try:
                    await conn.execute(statement)
                except sqlite3.OperationalError as e:
                    error_msg = str(e).lower()
                    # Ignore "duplicate column" and "already exists" errors
                    # These can happen when database.py already applied the migration
                    if 'duplicate column' in error_msg or 'already exists' in error_msg:
                        logger.debug("Skipping statement (already applied)",
                                    migration_name=migration_name,
                                    reason=str(e))
                        continue
                    # Ignore "no such table" errors for optional operations
                    elif 'no such table' in error_msg:
                        logger.debug("Skipping statement (table not found)",
                                    migration_name=migration_name,
                                    reason=str(e))
                        continue
                    else:
                        raise

            # Record migration as completed
            async with conn.execute("""
                INSERT INTO schema_migrations (migration_name)
                VALUES (?)
            """, (migration_name,)):
                pass

            await conn.commit()

            logger.info("Migration completed successfully", migration_name=migration_name)

        except Exception as e:
            logger.error("Failed to run migration",
                        migration_name=migration_name,
                        error=str(e))
            raise

    def _parse_sql_statements(self, sql_content: str) -> List[str]:
        """Parse SQL content into individual statements."""
        statements = []
        current = []

        for line in sql_content.split('\n'):
            # Remove comments
            if '--' in line:
                line = line[:line.index('--')]
            line = line.strip()
            if not line:
                continue

            current.append(line)

            if line.endswith(';'):
                stmt = ' '.join(current).strip()
                if stmt and stmt != ';':
                    statements.append(stmt)
                current = []

        # Add any remaining statement
        if current:
            stmt = ' '.join(current).strip()
            if stmt and stmt != ';':
                statements.append(stmt)

        return statements
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get migration status information."""
        try:
            if not self.database:
                return {"error": "Database not initialized"}
            
            completed = await self._get_completed_migrations()
            available_files = self._get_migration_files()
            
            available_names = {f.stem for f in available_files}
            pending_names = available_names - completed
            
            return {
                "total_migrations": len(available_files),
                "completed_count": len(completed),
                "pending_count": len(pending_names),
                "completed_migrations": sorted(completed),
                "pending_migrations": sorted(pending_names),
                "migration_status": "up_to_date" if not pending_names else "pending"
            }
            
        except Exception as e:
            logger.error("Failed to get migration status", error=str(e))
            raise
    
    async def force_run_migration(self, migration_name: str):
        """Force run a specific migration (for development/debugging)."""
        try:
            if not self.database:
                raise RuntimeError("Database not initialized")
            
            migration_file = self.migrations_path / f"{migration_name}.sql"
            
            if not migration_file.exists():
                raise ValueError(f"Migration file not found: {migration_name}")
            
            await self._run_migration_file(migration_file, migration_name)
            logger.info("Forced migration run completed", migration_name=migration_name)
            
        except Exception as e:
            logger.error("Failed to force run migration", 
                        migration_name=migration_name, error=str(e))
            raise