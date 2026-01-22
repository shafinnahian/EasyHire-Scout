#!/usr/bin/env python3
"""
Initialize the database by creating all tables.
Run this script once to set up the database schema.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from easyhire_scout.database import init_db


def main():
    """Initialize the database schema."""
    print("Initializing database...")
    try:
        init_db()
        print("✓ Database initialized successfully!")
        print("All tables have been created.")
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
