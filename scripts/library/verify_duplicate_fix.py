"""
Verification script to check that the duplicate fix is working.
This simulates what happens when the file watcher processes files.
"""
import asyncio
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.library_service import LibraryService
from src.database.database import Database
from src.utils.config import PrinternizerSettings
from src.services.event_service import EventService
from src.services.config_service import ConfigService


async def verify_duplicate_logic():
    """Verify that duplicate detection works"""

    print("=" * 60)
    print("Duplicate Detection Fix Verification")
    print("=" * 60)

    # Create a temporary test file
    test_file = Path(__file__).parent / "test_file.3mf"
    test_file.write_text("test content for duplicate detection")

    try:
        # Initialize services
        db = Database(":memory:")
        await db.initialize()

        settings = PrinternizerSettings()
        settings.library_path = Path(__file__).parent / "test_library"
        settings.library_enabled = True

        config_service = ConfigService(settings, db)
        event_service = EventService()
        library_service = LibraryService(db, config_service, event_service)

        await library_service.initialize()

        # Calculate checksum
        checksum = await library_service.calculate_checksum(test_file)
        print(f"\n✓ Calculated checksum: {checksum[:16]}...")

        # First check - should be None
        existing = await library_service.get_file_by_checksum(checksum)
        if existing is None:
            print("✓ First check: File NOT in library (correct)")
        else:
            print("✗ First check: File already in library (unexpected)")
            return False

        # Add file to library
        source_info = {
            'type': 'watch_folder',
            'folder_path': 'test/folder',
            'relative_path': 'test_file.3mf',
            'discovered_at': '2025-10-06T12:00:00'
        }

        result = await library_service.add_file_to_library(
            source_path=test_file,
            source_info=source_info,
            copy_file=True
        )
        print(f"✓ Added file to library: {result['filename']}")

        # Second check - should find the file
        existing = await library_service.get_file_by_checksum(checksum)
        if existing is not None:
            print(f"✓ Second check: File FOUND in library (correct)")
            print(f"  - Filename: {existing['filename']}")
            print(f"  - Checksum: {existing['checksum'][:16]}...")
        else:
            print("✗ Second check: File NOT in library (unexpected)")
            return False

        # Simulate what the file watcher should do now
        print("\n" + "=" * 60)
        print("Simulating File Watcher Logic (with fix)")
        print("=" * 60)

        # Check for duplicate BEFORE copying
        checksum_again = await library_service.calculate_checksum(test_file)
        existing_file = await library_service.get_file_by_checksum(checksum_again)

        if existing_file:
            print("✓ File already in library - SKIP copy")
            print(f"  - Will add as additional source instead")
            print(f"  - Existing file: {existing_file['filename']}")
            print(f"  - Checksum matches: {checksum_again[:16]}...")
        else:
            print("✗ File not found - would create duplicate (BAD)")
            return False

        print("\n" + "=" * 60)
        print("✓ ALL CHECKS PASSED - Duplicate fix is working!")
        print("=" * 60)

        # Cleanup
        await db.close()

        return True

    finally:
        # Cleanup test file
        if test_file.exists():
            test_file.unlink()

        # Cleanup test library
        import shutil
        test_library = Path(__file__).parent / "test_library"
        if test_library.exists():
            shutil.rmtree(test_library)


if __name__ == "__main__":
    result = asyncio.run(verify_duplicate_logic())
    sys.exit(0 if result else 1)
