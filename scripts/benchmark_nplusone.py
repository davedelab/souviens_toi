import sqlite3
import json
import time
import os

DB_FILE = "benchmark_temp.db"

def setup_db(num_rows=1000):
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    conn = sqlite3.connect(DB_FILE)
    conn.execute("CREATE TABLE clips (id INTEGER PRIMARY KEY, raw_text TEXT, tags TEXT, categories TEXT)")
    data = [(i, f"text {i}", f"tag{i}", f"cat{i}") for i in range(num_rows)]
    conn.executemany("INSERT INTO clips VALUES (?, ?, ?, ?)", data)
    conn.commit()
    return conn

def benchmark_nplusone(conn, ids):
    start = time.time()
    results = []
    for i in ids:
        row = conn.execute("SELECT raw_text, tags FROM clips WHERE id=?", (i,)).fetchone()
        if row:
            results.append(row)
    end = time.time()
    return end - start, len(results)

def benchmark_json_each(conn, ids):
    start = time.time()
    # Simulated optimization: fetch all at once
    query = "SELECT id, raw_text, tags FROM clips WHERE id IN (SELECT value FROM json_each(?))"
    rows = conn.execute(query, (json.dumps(ids),)).fetchall()
    # Map them to maintain order if needed, or just simulate the fetch
    results = {row[0]: row[1:] for row in rows}
    # To strictly follow the original logic where we iterate over IDs
    final_results = []
    for i in ids:
        if i in results:
            final_results.append(results[i])
    end = time.time()
    return end - start, len(final_results)

def main():
    num_rows = 5000
    ids_to_fetch = list(range(0, num_rows, 5)) # Fetch 1000 rows

    conn = setup_db(num_rows)

    print(f"Benchmarking with {len(ids_to_fetch)} IDs...")

    t1, count1 = benchmark_nplusone(conn, ids_to_fetch)
    print(f"N+1 approach: {t1:.4f} seconds ({count1} rows)")

    t2, count2 = benchmark_json_each(conn, ids_to_fetch)
    print(f"json_each approach: {t2:.4f} seconds ({count2} rows)")

    if t2 < t1:
        improvement = (t1 - t2) / t1 * 100
        print(f"Improvement: {improvement:.2f}%")
    else:
        print("No improvement detected in this environment.")

    conn.close()
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

if __name__ == "__main__":
    main()
