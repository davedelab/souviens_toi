import re
path = 'memex_next/ui/editor.py'
with open(path, 'r') as f:
    content = f.read()

content = content.replace('import tkinter as tk', 'import io\nimport tkinter as tk')
content = content.replace('from ..config import load_config, save_config', 'from ..config import load_config, save_config, SEPARATOR')
content = content.replace('BytesIO(', 'io.BytesIO(')

# Fix E701/E702/E722
content = re.sub(r'if (.+): (return|continue|break|pass)$', r'if \1:\n            \2', content, flags=re.MULTILINE)
content = content.replace('except:', 'except Exception:')
content = content.replace('if prefill: self._apply_prefill(prefill)', 'if prefill:\n            self._apply_prefill(prefill)')
content = content.replace('if err: mb.showerror("IA", str(err)); return', 'if err:\n                mb.showerror("IA", str(err))\n                return')
content = content.replace('if res: self.title_var.set(res); self._toast("Titre IA appliqué")', 'if res:\n                self.title_var.set(res)\n                self._toast("Titre IA appliqué")')
content = content.replace('if added: self._toast(f"{added} fichier(s) joint(s)")', 'if added:\n            self._toast(f"{added} fichier(s) joint(s)")')
content = content.replace('for w in self._thumb_container.winfo_children(): w.destroy()', 'for w in self._thumb_container.winfo_children():\n            w.destroy()')
content = content.replace('if not sel: return None', 'if not sel:\n                return None')

with open(path, 'w') as f:
    f.write(content)
