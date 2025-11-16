CREATE TABLE IF NOT EXISTS clips (
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
);
CREATE INDEX IF NOT EXISTS idx_clips_ts ON clips(ts);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    clip_id INTEGER NOT NULL,
    filename TEXT,
    mime TEXT,
    size INTEGER,
    sha256 TEXT UNIQUE,
    data BLOB,
    FOREIGN KEY (clip_id) REFERENCES clips(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_files_clip_id ON files(clip_id);

CREATE TABLE IF NOT EXISTS source_urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE,
    clip_id INTEGER,
    created_at INTEGER,
    FOREIGN KEY (clip_id) REFERENCES clips(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_urls_url ON source_urls(url);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    note TEXT,
    status TEXT DEFAULT 'pending',
    priority TEXT DEFAULT 'medium',
    due_at INTEGER,
    clip_id INTEGER,
    created_at INTEGER,
    FOREIGN KEY (clip_id) REFERENCES clips(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_at);
