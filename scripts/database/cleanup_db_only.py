"""
Quick script to clear only library database tables.
Use when files have been manually removed.
"""
import asyncio
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.database import Database


async def clear_library_database():
    """Clear library-related tables in the database"""
    db_path = Path(__file__).parent.parent / "data" / "printernizer.db"

    if not db_path.exists():
        print("Database not found!")
        return False

    print("Clearing library database tables...")

    db = Database(str(db_path))
    await db.initialize()

    try:
        # Get counts before deletion
        result = await db._fetch_one("SELECT COUNT(*) as count FROM library_files")
        file_count = result['count'] if result else 0

        result = await db._fetch_one("SELECT COUNT(*) as count FROM library_file_sources")
        source_count = result['count'] if result else 0

        print(f"Found {file_count} library files and {source_count} sources")

        # Clear library tables
        tables_to_clear = [
            'collection_members',
            'collections',
            'library_file_sources',
            'library_files'
        ]

        for table in tables_to_clear:
            print(f"Clearing {table}...")
            await db._execute_write(f"DELETE FROM {table}")
            print(f"{table} cleared")

        print("\nDatabase tables cleared successfully!")

        # Verify
        result = await db._fetch_one("SELECT COUNT(*) as count FROM library_files")
        remaining = result['count'] if result else 0

        if remaining == 0:
            print("Verification: Database is clean")
        else:
            print(f"Warning: {remaining} records still remain")

        return True

    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        await db.close()


if __name__ == "__main__":
    result = asyncio.run(clear_library_database())
    sys.exit(0 if result else 1)
