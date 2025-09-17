#!/usr/bin/env python3
"""
Insert a test job into the database for testing purposes.
"""
import sqlite3
import sys
from datetime import datetime, timedelta
from uuid import uuid4

def insert_test_job():
    """Insert a test job for button testing."""
    db_path = "data/printernizer.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get existing printer ID (try bambu_lab first, then any printer)
        cursor.execute("SELECT id FROM printers WHERE type LIKE '%bambu%' LIMIT 1")
        printer_result = cursor.fetchone()

        if not printer_result:
            cursor.execute("SELECT id FROM printers LIMIT 1")
            printer_result = cursor.fetchone()

        if not printer_result:
            print("No Bambu Lab printer found in database")
            return False

        printer_id = printer_result[0]
        print(f"Using printer ID: {printer_id}")

        # Insert test job
        now = datetime.now()
        start_time = now - timedelta(minutes=90)

        # Get printer type
        cursor.execute("SELECT type FROM printers WHERE id = ?", (printer_id,))
        printer_type_result = cursor.fetchone()
        printer_type = printer_type_result[0] if printer_type_result else 'unknown'

        # Simple job data that should work
        cursor.execute("""
            INSERT INTO jobs (
                printer_id, printer_type, job_name, status, progress, is_business
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            printer_id,
            printer_type,
            'test_model_button_test.3mf',
            'printing',
            75.5,
            1
        ))

        job_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f"Test job inserted successfully with ID: {job_id}")
        print(f"Job name: test_model_button_test.3mf")
        print(f"Status: printing")
        print(f"Progress: 75.5%")

        return True

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = insert_test_job()
    sys.exit(0 if success else 1)