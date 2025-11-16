import os, json, pathlib
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DB_FILE      = BASE_DIR / "souviens_toi.db"
CONFIG_FILE  = BASE_DIR / "souviens_config.json"
SEPARATOR    = "\n---\n"

def load_config():
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_config(data: dict):
    CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
