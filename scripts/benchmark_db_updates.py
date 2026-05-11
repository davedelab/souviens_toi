import sqlite3
import time
import json

def setup_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE clips (id INTEGER PRIMARY KEY, title TEXT, raw_text TEXT, tags TEXT, categories TEXT, ts INTEGER)")
    # Insert 500 rows
    data = []
    now = int(time.time())
    for i in range(500):
        data.append((f"Title {i}", f"Raw text {i}", "", "", now))
    conn.executemany("INSERT INTO clips (title, raw_text, tags, categories, ts) VALUES (?, ?, ?, ?, ?)", data)
    conn.commit()
    return conn

# Mock AI functions
def ai_generate_tags(text, lang='fr', count=5):
    # Simulate some work
    return [f"tag{i}" for i in range(count)]

def ai_generate_categories(text, user_cats, lang='fr', max_n=2):
    return user_cats[:max_n]

def ai_generate_title(text, lang='fr', max_len=80):
    return "New Title"

# Current implementation logic
def current_ai_tags_missing(conn):
    rows = conn.execute("SELECT id, raw_text FROM clips WHERE tags='' OR tags='non traitée par l IA'").fetchall()
    updated = 0
    for i, raw in rows:
        tags = ai_generate_tags(raw or '')
        conn.execute("UPDATE clips SET tags=? WHERE id=?", (', '.join(tags), i))
        updated += 1
    conn.commit()
    return updated

def current_ai_all_selected(conn, ids):
    lang = 'fr'
    user_cats = ['cat1', 'cat2']
    count = 5
    max_len = 80
    updated = 0
    for i in ids:
        row = conn.execute("SELECT raw_text, tags FROM clips WHERE id=?", (i,)).fetchone()
        if not row: continue
        raw, existing_tags = row
        title = ai_generate_title(raw or '', lang=lang, max_len=max_len)
        tags  = ai_generate_tags(raw or '', lang=lang, count=count)
        cats  = ai_generate_categories(raw or '', user_cats=user_cats, lang=lang, max_n=2)
        existing_list = [p.strip() for p in (existing_tags or '').replace(';', ',').split(',') if p.strip()]
        merged_tags = list(dict.fromkeys(existing_list + tags))
        conn.execute(
            "UPDATE clips SET title=COALESCE(?, title), tags=?, categories=? WHERE id=?",
            (title, ', '.join(merged_tags), ', '.join(cats), i)
        )
        updated += 1
    conn.commit()
    return updated

# Optimized implementation logic
def optimized_ai_tags_missing(conn):
    rows = conn.execute("SELECT id, raw_text FROM clips WHERE tags='' OR tags='non traitée par l IA'").fetchall()
    updates = []
    for i, raw in rows:
        tags = ai_generate_tags(raw or '')
        updates.append((', '.join(tags), i))
    conn.executemany("UPDATE clips SET tags=? WHERE id=?", updates)
    conn.commit()
    return len(updates)

def optimized_ai_all_selected(conn, ids):
    lang = 'fr'
    user_cats = ['cat1', 'cat2']
    count = 5
    max_len = 80

    # Use json_each
    rows = conn.execute("SELECT id, raw_text, tags FROM clips WHERE id IN (SELECT value FROM json_each(?))", (json.dumps(ids),)).fetchall()

    updates = []
    for i, raw, existing_tags in rows:
        title = ai_generate_title(raw or '', lang=lang, max_len=max_len)
        tags  = ai_generate_tags(raw or '', lang=lang, count=count)
        cats  = ai_generate_categories(raw or '', user_cats=user_cats, lang=lang, max_n=2)
        existing_list = [p.strip() for p in (existing_tags or '').replace(';', ',').split(',') if p.strip()]
        merged_tags = list(dict.fromkeys(existing_list + tags))
        updates.append((title, ', '.join(merged_tags), ', '.join(cats), i))

    conn.executemany(
        "UPDATE clips SET title=COALESCE(?, title), tags=?, categories=? WHERE id=?",
        updates
    )
    conn.commit()
    return len(updates)

def run_benchmark():
    print("Starting benchmark...")
    # Test tags_missing
    conn = setup_db()
    start = time.perf_counter()
    current_ai_tags_missing(conn)
    end = time.perf_counter()
    current_tags_time = end - start
    print(f"Current ai_tags_missing (500 rows): {current_tags_time:.4f}s")

    conn = setup_db()
    start = time.perf_counter()
    optimized_ai_tags_missing(conn)
    end = time.perf_counter()
    optimized_tags_time = end - start
    print(f"Optimized ai_tags_missing (500 rows): {optimized_tags_time:.4f}s")
    print(f"Improvement: {(current_tags_time - optimized_tags_time) / current_tags_time * 100:.2f}%")

    # Test all_selected
    ids = list(range(1, 501))
    conn = setup_db()
    start = time.perf_counter()
    current_ai_all_selected(conn, ids)
    end = time.perf_counter()
    current_all_time = end - start
    print(f"Current ai_all_selected (500 rows): {current_all_time:.4f}s")

    conn = setup_db()
    start = time.perf_counter()
    optimized_ai_all_selected(conn, ids)
    end = time.perf_counter()
    optimized_all_time = end - start
    print(f"Optimized ai_all_selected (500 rows): {optimized_all_time:.4f}s")
    print(f"Improvement: {(current_all_time - optimized_all_time) / current_all_time * 100:.2f}%")

if __name__ == "__main__":
    run_benchmark()
