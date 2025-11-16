### memex_next/db.py
import sqlite3, pathlib
from .config import DB_FILE

def create_conn():
    c = sqlite3.connect(DB_FILE, timeout=10)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=5000")
    c.execute("PRAGMA synchronous=NORMAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c

def init_db():
    conn = create_conn()
    schema = (pathlib.Path(__file__).parent / "resources" / "schema.sql").read_text(encoding="utf-8")
    conn.executescript(schema)
    conn.commit()
    return conn
