"""
Database initialization script.
Creates all tables and optionally loads directory data.
"""
import json
import os
import sys

# Ensure the app package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.config import Config

app = create_app()


def create_tables():
    """Create all database tables."""
    with app.app_context():
        db.create_all()
        print('✓ All database tables created successfully.')
        print(f'  Database: {app.config["SQLALCHEMY_DATABASE_URI"]}')


def load_directory_data():
    """Print directory stats from the JSON data file."""
    data_path = Config.DIRECTORIES_DATA_PATH
    if not os.path.exists(data_path):
        print(f'⚠ Directory data file not found: {data_path}')
        return

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    meta = data.get('meta', {})
    directories = data.get('directories', [])

    print(f'\nDirectory Data Summary:')
    print(f'  Title: {meta.get("title", "N/A")}')
    print(f'  Total entries: {meta.get("total_entries", len(directories))}')
    print(f'  Fields tracked: {", ".join(meta.get("fields_tracked", []))}')

    # Count by difficulty
    from collections import Counter
    difficulties = Counter(d.get('difficulty', 'unknown') for d in directories)
    print(f'\n  By difficulty:')
    for diff, count in difficulties.most_common():
        print(f'    {diff}: {count}')

    # Count by category
    categories = Counter(d.get('category', 'unknown') for d in directories)
    print(f'\n  By category:')
    for cat, count in categories.most_common():
        print(f'    {cat}: {count}')

    # Count requiring CAPTCHA
    captcha_count = sum(1 for d in directories if d.get('requires_captcha'))
    print(f'\n  Directories requiring CAPTCHA: {captcha_count}/{len(directories)}')

    # List names
    print(f'\n  Directory list:')
    for i, d in enumerate(directories, 1):
        print(f'    {i:2d}. {d["name"]} ({d.get("difficulty", "?")})')


if __name__ == '__main__':
    create_tables()
    load_directory_data()
