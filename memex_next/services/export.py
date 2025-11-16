### memex_next/services/export.py
import json, os, pathlib, datetime as dt
from typing import List, Dict, Any
from ..models import Clip

def clip_to_markdown(clip: Dict[str, Any]) -> str:
    title   = clip.get("title", "")
    date    = dt.datetime.fromtimestamp(clip.get("ts", 0), tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
    tags    = [t.strip() for t in clip.get("tags", "").replace(";", ",").split(",") if t.strip()]
    cats    = [c.strip() for c in clip.get("categories", "").split(",") if c.strip()]
    typ     = clip.get("type", "note")
    source  = clip.get("source", "")
    body    = clip.get("raw_text", "")
    front   = [
        "---",
        f'title: "{title.replace('"', "'")}"',
        f'date: "{date}"',
        f'tags: [{", ".join(tags)}]',
        f'categories: [{", ".join(cats)}]',
        f'type: {typ}',
        f'source: "{source}"',
        "---",
        ""
    ]
    return "\n".join(front) + body

def safe_filename(s: str) -> str:
    import re
    return re.sub(r'[\\/:*?"<>|]+', '_', s)[:80] or "note"

def export_selected_md(clips: List[Dict[str, Any]], folder: pathlib.Path, cfg: Dict[str, Any]) -> int:
    folder = pathlib.Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    count = 0
    for clip in clips:
        name = safe_filename(clip.get("title"))
        if cfg.get("md_date_prefix"):
            date = dt.datetime.fromtimestamp(clip["ts"], tz=dt.timezone.utc).strftime("%Y-%m-%d")
            name = f"{date}_{name}"
        path = folder / f"{name}.md"
        path.write_text(clip_to_markdown(clip), encoding="utf-8")
        count += 1
    return count

def export_json(clips: List[Dict[str, Any]], path: pathlib.Path):
    path.write_text(json.dumps(clips, ensure_ascii=False, indent=2), encoding="utf-8")
