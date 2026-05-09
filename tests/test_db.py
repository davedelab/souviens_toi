import sqlite3
import pathlib
from unittest.mock import patch
from memex_next.db import init_db

def test_init_db_creates_tables(tmp_path):
    db_file = tmp_path / "test.db"
    with patch("memex_next.db.DB_FILE", db_file):
        conn = init_db()

        # Check if tables exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        assert "clips" in tables
        assert "files" in tables
        assert "source_urls" in tables
        assert "tasks" in tables

        # Check if reminder_days column exists in tasks
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "reminder_days" in columns

        conn.close()

def test_init_db_migration(tmp_path):
    db_file = tmp_path / "migration_test.db"

    # Pre-create database without reminder_days column in tasks
    # We should include all other columns to avoid errors with indices in schema.sql
    conn = sqlite3.connect(db_file)
    conn.execute("""
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            note TEXT,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            due_at INTEGER,
            clip_id INTEGER,
            created_at INTEGER
        )
    """)
    conn.commit()
    conn.close()

    with patch("memex_next.db.DB_FILE", db_file):
        # This should trigger the migration logic in init_db
        conn = init_db()

        # Check if reminder_days column was added
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "reminder_days" in columns

        conn.close()
