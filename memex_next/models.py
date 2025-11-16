from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class Clip:
    id: Optional[int] = None
    ts: int = 0
    source: str = ""
    title: str = ""
    type: str = "note"
    raw_text: str = ""
    summary: str = ""
    tags: str = ""
    categories: str = ""
    read_later: int = 0

@dataclass
class Task:
    id: Optional[int] = None
    title: str = ""
    note: str = ""
    status: str = "pending"
    priority: str = "medium"
    due_at: Optional[int] = None
    clip_id: Optional[int] = None
    created_at: int = 0

@dataclass
class File:
    id: Optional[int] = None
    clip_id: int = 0
    filename: str = ""
    mime: str = ""
    size: int = 0
    sha256: str = ""
    data: bytes = b""
