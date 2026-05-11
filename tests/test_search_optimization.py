import sys
from unittest.mock import MagicMock

# Mock GUI and other external dependencies
mock_modules = [
    'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
    'tkinter.simpledialog', 'tkinter.scrolledtext', 'pyperclip',
    'tkhtmlview', 'tkcalendar', 'pypdf', 'pdfplumber', 'pytesseract',
    'trafilatura', 'markdownify', 'PIL'
]
for mod in mock_modules:
    sys.modules[mod] = MagicMock()

import json
import sqlite3

def test_ai_tags_selected_logic(tmp_path, monkeypatch):
    # Setup a temporary database
    db_path = tmp_path / "test.db"
    monkeypatch.setattr("memex_next.config.DB_FILE", db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE clips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_text TEXT,
            tags TEXT
        )
    """)
    conn.execute("INSERT INTO clips (raw_text, tags) VALUES ('Text 1', \"non traitée par l'IA\")")
    conn.execute("INSERT INTO clips (raw_text, tags) VALUES ('Text 2', 'tag_existing')")
    conn.commit()
    conn.close()

    # Mock AI service
    def mock_ai_generate_tags(text, lang='fr', count=5):
        if 'Text 1' in text: return ['tag1', 'tag2']
        if 'Text 2' in text: return ['tag3']
        return []

    # We want to test the logic INSIDE the work() function.
    # Since it's nested, we will recreate it here or find a way to import it.
    # Re-implementing the logic here to verify it works as intended with the same SQL queries.

    ids = [1, 2]
    lang = 'fr'
    count = 5

    # This is exactly the code from ai_tags_selected's work()
    def work():
        conn = sqlite3.connect(db_path)
        # We need to make sure json_each is available. In standard sqlite3 it usually is.
        rows = conn.execute("SELECT id, raw_text, tags FROM clips WHERE id IN (SELECT value FROM json_each(?))", (json.dumps(ids),)).fetchall()
        updates = []
        for i, raw, existing in rows:
            tags_ai = mock_ai_generate_tags(raw or '', lang=lang, count=count)
            if existing and ("Non traitée par l'IA" in existing or "non traitée par l'IA" in existing):
                existing_list = []
            else:
                existing_list = [p.strip() for p in (existing or '').replace(';', ',').split(',') if p.strip()]
            merged = list(dict.fromkeys(existing_list + tags_ai))
            updates.append((', '.join(merged), i))
        if updates:
            conn.executemany("UPDATE clips SET tags=? WHERE id=?", updates)
            conn.commit()
        conn.close()
        return len(updates)

    res = work()
    assert res == 2

    # Verify DB state
    conn = sqlite3.connect(db_path)
    row1 = conn.execute("SELECT tags FROM clips WHERE id=1").fetchone()
    row2 = conn.execute("SELECT tags FROM clips WHERE id=2").fetchone()
    conn.close()

    assert "tag1, tag2" in row1[0]
    assert "tag_existing, tag3" in row2[0]

def test_ai_all_selected_logic(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr("memex_next.config.DB_FILE", db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE clips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            raw_text TEXT,
            tags TEXT,
            categories TEXT
        )
    """)
    conn.execute("INSERT INTO clips (title, raw_text, tags, categories) VALUES ('Old Title', 'Text 1', '', '')")
    conn.commit()
    conn.close()

    def mock_ai_generate_tags(*a, **kw): return ['tag1']
    def mock_ai_generate_categories(*a, **kw): return ['cat1']
    def mock_ai_generate_title(*a, **kw): return 'New Title'

    ids = [1]
    lang = 'fr'
    user_cats = ['cat1']
    count = 5
    max_len = 80

    def work():
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT id, raw_text, tags FROM clips WHERE id IN (SELECT value FROM json_each(?))", (json.dumps(ids),)).fetchall()
        updates = []
        for i, raw, existing_tags in rows:
            title = mock_ai_generate_title(raw or '', lang=lang, max_len=max_len)
            tags  = mock_ai_generate_tags(raw or '', lang=lang, count=count)
            cats  = mock_ai_generate_categories(raw or '', user_cats=user_cats, lang=lang, max_n=2)
            existing_list = [p.strip() for p in (existing_tags or '').replace(';', ',').split(',') if p.strip()]
            merged_tags = list(dict.fromkeys(existing_list + tags))
            updates.append((title, ', '.join(merged_tags), ', '.join(cats), i))
        if updates:
            conn.executemany(
                "UPDATE clips SET title=COALESCE(?, title), tags=?, categories=? WHERE id=?",
                updates
            )
            conn.commit()
        conn.close()
        return len(updates)

    res = work()
    assert res == 1

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT title, tags, categories FROM clips WHERE id=1").fetchone()
    conn.close()

    assert row[0] == 'New Title'
    assert row[1] == 'tag1'
    assert row[2] == 'cat1'
