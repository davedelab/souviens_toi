import re
import os

def fix_export():
    p = 'memex_next/services/export.py'
    with open(p, 'r') as f: content = f.read()
    old = 'f\'title: "{title.replace(\'\"\', "\'")}"\','
    new = "safe_title = title.replace('\"', \"'\")\n    front   = [\n        \"---\",\n        f'title: \"{safe_title}\"',"
    content = content.replace('front   = [\n        "---",\n        ' + old, new)
    with open(p, 'w') as f: f.write(content)

def fix_editor():
    p = 'memex_next/ui/editor.py'
    with open(p, 'r') as f: content = f.read()
    if 'import io' not in content:
        content = content.replace('import tkinter as tk', 'import io\nimport tkinter as tk')
    content = content.replace('from ..config import load_config, save_config', 'from ..config import load_config, save_config, SEPARATOR')
    content = content.replace('BytesIO(', 'io.BytesIO(')
    content = content.replace('if prefill: self._apply_prefill(prefill)', 'if prefill:\n            self._apply_prefill(prefill)')
    # remove local imports of ai things that are already at top
    content = re.sub(r'\n +from \.\.ai import .+', '', content)
    with open(p, 'w') as f: f.write(content)

def fix_search():
    p = 'memex_next/ui/search.py'
    with open(p, 'r') as f: content = f.read()
    content = content.replace('from ..config import load_config, save_config', 'from ..config import load_config, save_config, SEPARATOR')
    content = content.replace('from ..ai import ai_generate_tags, ai_generate_categories', 'from ..ai import ai_generate_tags, ai_generate_categories, ai_generate_title')
    content = content.replace("sep = (\"\\n\" + SEPARATOR + \"\\n\") if current else ''", "sep = (\"\\n\" + SEPARATOR + \"\\n\") if current else \"\"")
    # remove local imports of ai things that are already at top
    content = re.sub(r'\n +from \.\.ai import .+', '', content)
    with open(p, 'w') as f: f.write(content)

def fix_app():
    p = 'memex_next/ui/app.py'
    with open(p, 'r') as f: content = f.read()
    # Hoist all AI imports to top
    content = content.replace('from ..ai import ai_generate_tags, ai_generate_title',
                              'from ..ai import ai_generate_tags, ai_generate_title, ai_generate_categories, ai_suggest_new_categories')
    # Remove local ones
    content = re.sub(r'\n +from \.\.ai import .+', '', content)
    # Multi-line imports
    content = content.replace('import tkinter as tk, tkinter.ttk as ttk, threading, time, queue, datetime as dt, sys, pathlib',
                              'import tkinter as tk\nimport tkinter.ttk as ttk\nimport threading\nimport time\nimport queue\nimport datetime as dt\nimport sys\nimport pathlib')
    # SEPARATOR issue
    content = content.replace('sep = ("\\n" + SEPARATOR + "\\n") if current else \'\'', 'sep = ("\\n" + SEPARATOR + "\\n") if current else ""')

    # first_clip_id scoping
    content = content.replace('first_clip_id = None', 'self._first_clip_id_for_session = None')
    content = content.replace('if first_clip_id is None:', 'if self._first_clip_id_for_session is None:')
    content = content.replace('first_clip_id = clip_id', 'self._first_clip_id_for_session = clip_id')
    content = content.replace('if first_clip_id:', 'if self._first_clip_id_for_session:')
    content = content.replace('EditClipWindow(self, first_clip_id)', 'EditClipWindow(self, self._first_clip_id_for_session)')

    # Initialize it in __init__
    if 'self._first_clip_id_for_session = None' not in content:
        content = content.replace('self._search_win = None', 'self._search_win = None\n        self._first_clip_id_for_session = None')

    with open(p, 'w') as f: f.write(content)

fix_export()
fix_editor()
fix_search()
fix_app()
