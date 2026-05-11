path = 'memex_next/ui/editor.py'
with open(path, 'r') as f: content = f.read()
if 'import io' not in content:
    content = content.replace('import tkinter as tk', 'import io\nimport tkinter as tk')
content = content.replace('from ..config import load_config, save_config', 'from ..config import load_config, save_config, SEPARATOR')
content = content.replace('BytesIO(', 'io.BytesIO(')
with open(path, 'w') as f: f.write(content)
