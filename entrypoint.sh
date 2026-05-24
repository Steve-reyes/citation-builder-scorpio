#!/bin/bash
set -e

echo "=== Citation Builder Entrypoint ==="

# Ensure directories exist
mkdir -p /app/instance /app/uploads

# Check if DB exists, if not create it
if [ ! -f /app/instance/citation.db ]; then
    echo "Creating fresh database..."
    cd /app
    python -c "
import sys, os
sys.path.insert(0, '/app')
from app import create_app
a = create_app()
with a.app_context():
    from app import db
    from app.models.business import Business
    from app.models.submission import DirectorySubmission
    db.create_all()
    print('✓ Database initialized at:', a.config['SQLALCHEMY_DATABASE_URI'])
"
fi

# Verify DB exists and is readable
if [ -f /app/instance/citation.db ]; then
    echo "✓ Database found: $(ls -lh /app/instance/citation.db | awk '{print $5}')"
else
    echo "ERROR: Failed to create database!"
    exit 1
fi

echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 "app:create_app()"
