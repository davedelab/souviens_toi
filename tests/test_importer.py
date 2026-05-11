import json
import pathlib
import sqlite3
import pytest
from unittest.mock import patch
from memex_next.services.importer import import_json
from memex_next.db import init_db

@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test.db"
    with patch("memex_next.db.DB_FILE", db_file):
        conn = init_db()
        conn.close()
    return db_file

def test_import_json_success(tmp_path, temp_db):
    # Prepare JSON file
    json_path = tmp_path / "clips.json"
    clips_data = [
        {
            "ts": 123456789,
            "source": "https://example.com",
            "title": "Test Clip",
            "type": "web",
            "raw_text": "Some text",
            "summary": "Summary",
            "tags": "tag1,tag2",
            "categories": "cat1",
            "read_later": 1
        }
    ]
    json_path.write_text(json.dumps(clips_data), encoding="utf-8")

    # Run import_json with patched DB_FILE
    with patch("memex_next.services.importer.DB_FILE", temp_db):
        import_json(json_path)

    # Verify database content
    conn = sqlite3.connect(temp_db)
    row = conn.execute("SELECT ts, source, title, type, raw_text, summary, tags, categories, read_later FROM clips").fetchone()
    conn.close()

    assert row == (123456789, "https://example.com", "Test Clip", "web", "Some text", "Summary", "tag1,tag2", "cat1", 1)

def test_import_json_not_a_list(tmp_path):
    json_path = tmp_path / "invalid.json"
    json_path.write_text(json.dumps({"not": "a list"}), encoding="utf-8")

    with pytest.raises(ValueError, match="JSON doit être une liste"):
        import_json(json_path)

def test_import_json_invalid_json(tmp_path):
    json_path = tmp_path / "broken.json"
    json_path.write_text("this is not json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        import_json(json_path)

def test_import_json_defaults(tmp_path, temp_db):
    # Prepare JSON file with minimal data
    json_path = tmp_path / "minimal.json"
    clips_data = [{}]
    json_path.write_text(json.dumps(clips_data), encoding="utf-8")

    # Run import_json with patched DB_FILE
    with patch("memex_next.services.importer.DB_FILE", temp_db):
        import_json(json_path)

    # Verify database content
    conn = sqlite3.connect(temp_db)
    row = conn.execute("SELECT ts, source, title, type, raw_text, summary, tags, categories, read_later FROM clips").fetchone()
    conn.close()

    # ts should be close to current time, others should be defaults
    assert isinstance(row[0], int)
    assert row[1] == ""      # source
    assert row[2] == ""      # title
    assert row[3] == "note"  # type
    assert row[4] == ""      # raw_text
    assert row[5] == ""      # summary
    assert row[6] == ""      # tags
    assert row[7] == ""      # categories
    assert row[8] == 0       # read_later
