"""
Cleanup script to remove all library files and clear database tables.
This prepares the system for a fresh start with the duplicate fix.
"""
import asyncio
import shutil
from pathlib import Path
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.database import Database


async def backup_database():
    """Create a backup of the current database"""
    db_path = Path(__file__).parent.parent / "data" / "printernizer.db"

    if not db_path.exists():
        print("Database not found, skipping backup")
        return None

    backup_path = db_path.parent / f"printernizer.db.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    print(f"Creating database backup...")
    print(f"   Source: {db_path}")
    print(f"   Backup: {backup_path}")

    shutil.copy2(db_path, backup_path)
    print(f"Backup created successfully")

    return backup_path


async def clear_library_files():
    """Remove all files from the library directory"""
    # Check both common locations
    library_paths = [
        Path("c:/app/data/library"),
        Path(__file__).parent.parent / "data" / "library"
    ]

    library_path = None
    for path in library_paths:
        if path.exists():
            library_path = path
            break

    if not library_path:
        print("Library directory not found, skipping file cleanup")
        return

    print(f"\nClearing library files from: {library_path}")

    # Count files before deletion
    file_count = sum(1 for _ in library_path.rglob("*.3mf")) + \
                 sum(1 for _ in library_path.rglob("*.stl")) + \
                 sum(1 for _ in library_path.rglob("*.gcode"))

    print(f"   Found {file_count} files to delete")

    # Remove models, printers, uploads directories
    directories_to_clear = ['models', 'printers', 'uploads']

    for dir_name in directories_to_clear:
        dir_path = library_path / dir_name
        if dir_path.exists():
            print(f"   Removing {dir_name}/...")
            shutil.rmtree(dir_path)
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   {dir_name}/ cleared")

    # Clear metadata but keep structure
    metadata_path = library_path / ".metadata"
    if metadata_path.exists():
        print(f"   Clearing .metadata/...")
        for item in metadata_path.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
                item.mkdir(parents=True, exist_ok=True)
            elif item.is_file():
                item.unlink()
        print(f"   .metadata/ cleared")

    print(f"Library files cleared")


async def clear_library_database():
    """Clear library-related tables in the database"""
    db_path = Path(__file__).parent.parent / "data" / "printernizer.db"

    if not db_path.exists():
        print("Database not found, skipping database cleanup")
        return

    print(f"\nClearing library database tables...")

    db = Database(str(db_path))
    await db.initialize()

    try:
        # Get counts before deletion
        result = await db._fetch_one("SELECT COUNT(*) as count FROM library_files")
        file_count = result['count'] if result else 0

        result = await db._fetch_one("SELECT COUNT(*) as count FROM library_file_sources")
        source_count = result['count'] if result else 0

        print(f"   Found {file_count} library files and {source_count} sources")

        # Clear library tables
        tables_to_clear = [
            'collection_members',
            'collections',
            'library_file_sources',
            'library_files'
        ]

        for table in tables_to_clear:
            print(f"   Clearing {table}...")
            await db._execute_write(f"DELETE FROM {table}")
            print(f"   {table} cleared")

        print(f"Database tables cleared")

    finally:
        await db.close()


async def verify_cleanup():
    """Verify that cleanup was successful"""
    print(f"\nVerifying cleanup...")

    # Check library directory
    library_paths = [
        Path("c:/app/data/library"),
        Path(__file__).parent.parent / "data" / "library"
    ]

    for library_path in library_paths:
        if library_path.exists():
            file_count = sum(1 for _ in library_path.rglob("*.3mf")) + \
                         sum(1 for _ in library_path.rglob("*.stl")) + \
                         sum(1 for _ in library_path.rglob("*.gcode"))

            if file_count == 0:
                print(f"   Library directory is empty: {library_path}")
            else:
                print(f"   Library still has {file_count} files: {library_path}")

    # Check database
    db_path = Path(__file__).parent.parent / "data" / "printernizer.db"
    if db_path.exists():
        db = Database(str(db_path))
        await db.initialize()

        try:
            result = await db._fetch_one("SELECT COUNT(*) as count FROM library_files")
            file_count = result['count'] if result else 0

            if file_count == 0:
                print(f"   Database library_files table is empty")
            else:
                print(f"   Database still has {file_count} library files")
        finally:
            await db.close()

    print(f"Verification complete")


async def main():
    """Main cleanup process"""
    print("=" * 70)
    print("Library Cleanup Script")
    print("=" * 70)
    print()
    print("WARNING: This will delete all library files and database records!")
    print("This prepares the system for re-adding files with the duplicate fix.")
    print()

    # Confirm action
    response = input("Continue with cleanup? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Cleanup cancelled")
        return

    print()
    print("Starting cleanup...")
    print()

    try:
        # Step 1: Backup database
        backup_path = await backup_database()

        # Step 2: Clear library files
        await clear_library_files()

        # Step 3: Clear database
        await clear_library_database()

        # Step 4: Verify
        await verify_cleanup()

        print()
        print("=" * 70)
        print("Cleanup completed successfully!")
        print("=" * 70)

        if backup_path:
            print(f"\nDatabase backup saved to: {backup_path}")

        print("\nNext steps:")
        print("   1. Restart the backend server")
        print("   2. Files from watch folders will be re-added without duplicates")
        print("   3. Check logs for 'File already in library, skipping copy' messages")

    except Exception as e:
        print()
        print("=" * 70)
        print(f"Error during cleanup: {e}")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
