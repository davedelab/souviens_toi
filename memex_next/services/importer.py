### memex_next/services/import.py
import json, pathlib, shutil, sqlite3
from datetime import datetime, timezone as TZ

def migrate_from_db(db_path: pathlib.Path) -> int:
    """Import sans verrou : lecture seule + INSERT un par un."""
    import sqlite3

    # 1. Ouvre la source en lecture seule (URI)
    src = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=1)
    src.execute("PRAGMA journal_mode=DELETE")

    # 2. Compte avant
    before = src.execute("SELECT COUNT(*) FROM clips").fetchone()[0]

    # 3. Ouvre la cible
    dst = sqlite3.connect("souviens_toi.db", timeout=10)
    dst.execute("PRAGMA journal_mode=WAL")

    # 4. Copie ligne par ligne (pas d’ATTACH)
    for row in src.execute("SELECT ts, source, title, type, raw_text, summary, tags, categories, read_later FROM clips"):
        dst.execute(
            "INSERT INTO clips(ts, source, title, type, raw_text, summary, tags, categories, read_later) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            row
        )
    dst.commit()

    # 5. Ferme
    src.close()
    after = dst.execute("SELECT COUNT(*) FROM clips").fetchone()[0]
    dst.close()
    return after - before

def import_json(path: pathlib.Path):
    clips = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(clips, list):
        raise ValueError("JSON doit être une liste")
    import sqlite3, time
    db = sqlite3.connect("souviens_toi.db")
    for c in clips:
        db.execute(
            "INSERT INTO clips(ts, source, title, type, raw_text, summary, tags, categories, read_later) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (c.get("ts", int(time.time())), c.get("source", ""), c.get("title", ""), c.get("type", "note"),
             c.get("raw_text", ""), c.get("summary", ""), c.get("tags", ""), c.get("categories", ""), c.get("read_later", 0))
        )
    db.commit()
    db.close()
