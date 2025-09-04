#!/bin/bash
# Printernizer Backend Entrypoint Script
# Handles database initialization and service startup

set -e

echo "Starting Printernizer backend..."
echo "Environment: ${ENVIRONMENT:-production}"
echo "Timezone: ${TZ:-Europe/Berlin}"

# Wait for database to be ready (if using external database)
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for external database to be ready..."
    # Add database wait logic here if needed
fi

# Initialize database if it doesn't exist
if [ ! -f "/app/data/printernizer.db" ]; then
    echo "Initializing database..."
    python -c "
import sqlite3
import os
from pathlib import Path

# Create data directory
data_dir = Path('/app/data')
data_dir.mkdir(exist_ok=True)

# Read and execute schema
with open('database_schema.sql', 'r') as f:
    schema = f.read()

# Create database
conn = sqlite3.connect('/app/data/printernizer.db')
conn.executescript(schema)
conn.close()

print('Database initialized successfully')
"
fi

# Set proper permissions
chown -R appuser:appuser /app/data /app/logs /app/backups 2>/dev/null || true

# Run database migrations if they exist
if [ -d "migrations" ]; then
    echo "Running database migrations..."
    python -m alembic upgrade head
fi

# Start the application
echo "Starting Printernizer API server..."
exec "$@"