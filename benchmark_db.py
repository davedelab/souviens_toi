import sqlite3
import time
import random
import string
import json

def setup_db(conn):
    conn.execute("""
    CREATE TABLE clips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER,
        source TEXT,
        title TEXT,
        type TEXT,
        raw_text TEXT,
        summary TEXT,
        tags TEXT,
        categories TEXT,
        read_later INTEGER DEFAULT 0
    )
    """)

    # Insert some dummy data
    data = []
    for i in range(1000):
        ts = int(time.time())
        raw_text = 'Some raw text content ' * 10
        data.append((ts, 'Source', 'Title ' + str(i), 'text', raw_text, '', "non traitée par l'IA", ''))

    conn.executemany("INSERT INTO clips (ts, source, title, type, raw_text, summary, tags, categories) VALUES (?,?,?,?,?,?,?,?)", data)
    conn.commit()

def mock_ai_tags(text):
    return ["tag1", "tag2", "tag3"]

def benchmark_pattern_a(conn, ids):
    """Many individual SELECTs + Many individual UPDATEs (like ai_tags_selected)"""
    start = time.perf_counter()
    updated = 0
    for i in ids:
        row = conn.execute("SELECT raw_text, tags FROM clips WHERE id=?", (i,)).fetchone()
        if not row: continue
        raw, existing = row
        tags_ai = mock_ai_tags(raw or '')

        if existing and ("Non traitée par l'IA" in existing or "non traitée par l'IA" in existing):
            existing_list = []
        else:
            existing_list = [p.strip() for p in (existing or '').replace(';', ',').split(',') if p.strip()]
        merged = list(dict.fromkeys(existing_list + tags_ai))

        conn.execute("UPDATE clips SET tags=? WHERE id=?", (', '.join(merged), i))
        updated += 1
    conn.commit()
    end = time.perf_counter()
    return end - start, updated

def benchmark_pattern_b(conn):
    """One big SELECT + Many individual UPDATEs (like ai_tags_missing)"""
    start = time.perf_counter()
    rows = conn.execute("SELECT id, raw_text FROM clips WHERE tags='' OR tags=\"non traitée par l'IA\"").fetchall()
    updated = 0
    for i, raw in rows:
        tags = mock_ai_tags(raw or '')
        conn.execute("UPDATE clips SET tags=? WHERE id=?", (', '.join(tags), i))
        updated += 1
    conn.commit()
    end = time.perf_counter()
    return end - start, updated

def benchmark_optimized(conn, ids):
    """One big SELECT + One executemany UPDATE (using json_each for large ID lists if needed)"""
    start = time.perf_counter()

    # Using json_each to avoid parameter limit and dynamic SQL
    rows = conn.execute("SELECT id, raw_text, tags FROM clips WHERE id IN (SELECT value FROM json_each(?))", (json.dumps(ids),)).fetchall()

    update_data = []
    for i, raw, existing in rows:
        tags_ai = mock_ai_tags(raw or '')
        if existing and ("Non traitée par l'IA" in existing or "non traitée par l'IA" in existing):
            existing_list = []
        else:
            existing_list = [p.strip() for p in (existing or '').replace(';', ',').split(',') if p.strip()]
        merged = list(dict.fromkeys(existing_list + tags_ai))
        update_data.append((', '.join(merged), i))

    conn.executemany("UPDATE clips SET tags=? WHERE id=?", update_data)
    conn.commit()

    end = time.perf_counter()
    return end - start, len(update_data)

def main():
    conn = sqlite3.connect(":memory:")
    setup_db(conn)

    ids = list(range(1, 1001))
    random.shuffle(ids)
    test_ids = ids[:500] # Benchmark with 500 items

    print(f"Benchmarking with {len(test_ids)} items...")

    time_a, count_a = benchmark_pattern_a(conn, test_ids)
    print(f"Pattern A (Individual SELECT & UPDATE): {time_a:.6f}s ({count_a} items)")

    # Reset tags for pattern B
    conn.execute("UPDATE clips SET tags=\"non traitée par l'IA\"")
    conn.commit()

    time_b, count_b = benchmark_pattern_b(conn)
    print(f"Pattern B (One SELECT, Individual UPDATEs): {time_b:.6f}s ({count_b} items)")

    # Reset tags for optimized
    conn.execute("UPDATE clips SET tags=\"non traitée par l'IA\"")
    conn.commit()

    time_opt, count_opt = benchmark_optimized(conn, test_ids)
    print(f"Optimized (Bulk SELECT & Bulk UPDATE): {time_opt:.6f}s ({count_opt} items)")

if __name__ == "__main__":
    main()
