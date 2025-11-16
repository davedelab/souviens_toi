### memex_next/services/import.py
import json, pathlib, shutil, sqlite3
from datetime import datetime, timezone as TZ

def migrate_from_db(db_path: pathlib.Path) -> int:
    """Importe les clips d’une ancienne base SQLite."""
    if not db_path.exists():
        raise RuntimeError("Fichier source introuvable")
    src = sqlite3.connect(db_path)
    dst = sqlite3.connect(pathlib.Path("souviens_toi.db"))
    cur = dst.execute("SELECT COUNT(*) FROM clips")
    before = cur.fetchone()[0]
    try:
        dst.execute(f"ATTACH DATABASE '{db_path}' AS old")
        dst.execute(
            "INSERT INTO clips(ts, source, title, type, raw_text, summary, tags, categories, read_later) "
            "SELECT ts, source, title, type, raw_text, summary, tags, categories, read_later FROM old.clips"
        )
        dst.execute("DETACH DATABASE old")
        dst.commit()
    finally:
        src.close()
        dst.close()
    after = dst.execute("SELECT COUNT(*) FROM clips").fetchone()[0]
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
