import time
import sqlite3
import json
import os
import tempfile

# Mocking the AI function
def mock_ai_generate_tags(text, lang='fr', count=5):
    return [f"tag_{i}" for i in range(count)]

def setup_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE clips (id INTEGER PRIMARY KEY, ts INTEGER, raw_text TEXT, tags TEXT, title TEXT, categories TEXT)")
    # Insert 1000 clips
    clips = []
    for i in range(1000):
        clips.append((int(time.time()), f"Some raw text {i}", "non traitée par l'IA"))
    conn.executemany("INSERT INTO clips (ts, raw_text, tags) VALUES (?, ?, ?)", clips)
    conn.commit()
    conn.close()

def original_logic(ids, db_path):
    conn = sqlite3.connect(db_path)
    updated = 0
    for i in ids:
        row = conn.execute("SELECT raw_text, tags FROM clips WHERE id=?", (i,)).fetchone()
        if not row: continue
        raw, existing = row
        tags_ai = mock_ai_generate_tags(raw or '')
        if existing and ("Non traitée par l'IA" in existing or "non traitée par l'IA" in existing):
            existing_list = []
        else:
            existing_list = [p.strip() for p in (existing or '').replace(';', ',').split(',') if p.strip()]
        merged = list(dict.fromkeys(existing_list + tags_ai))
        conn.execute("UPDATE clips SET tags=? WHERE id=?", (', '.join(merged), i))
        updated += 1
    conn.commit()
    conn.close()
    return updated

def optimized_logic(ids, db_path):
    conn = sqlite3.connect(db_path)
    # Using json_each for bulk fetch
    rows = conn.execute(
        "SELECT id, raw_text, tags FROM clips WHERE id IN (SELECT value FROM json_each(?))",
        (json.dumps(ids),)
    ).fetchall()

    updates = []
    for i, raw, existing in rows:
        tags_ai = mock_ai_generate_tags(raw or '')
        if existing and ("Non traitée par l'IA" in existing or "non traitée par l'IA" in existing):
            existing_list = []
        else:
            existing_list = [p.strip() for p in (existing or '').replace(';', ',').split(',') if p.strip()]
        merged = list(dict.fromkeys(existing_list + tags_ai))
        updates.append((', '.join(merged), i))

    conn.executemany("UPDATE clips SET tags=? WHERE id=?", updates)
    conn.commit()
    conn.close()
    return len(updates)

def run_benchmark():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    try:
        print(f"Setting up benchmark database at {db_path}...")
        setup_db(db_path)
        ids = list(range(1, 501)) # Benchmark with 500 items

        print(f"Running original logic with {len(ids)} items...")
        start = time.perf_counter()
        original_logic(ids, db_path)
        end = time.perf_counter()
        original_time = end - start
        print(f"Original logic: {original_time:.4f}s")

        # Reset tags for fair comparison
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE clips SET tags='non traitée par l''IA'")
        conn.commit()
        conn.close()

        print(f"Running optimized logic with {len(ids)} items...")
        start = time.perf_counter()
        optimized_logic(ids, db_path)
        end = time.perf_counter()
        optimized_time = end - start
        print(f"Optimized logic: {optimized_time:.4f}s")

        if original_time > 0:
            improvement = (original_time - optimized_time) / original_time * 100
            print(f"Improvement: {improvement:.2f}%")

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)

if __name__ == "__main__":
    run_benchmark()
