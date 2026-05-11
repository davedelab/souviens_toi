import re
import os

def fix_e701_e702(content):
    # Fix if cond: return/continue/break/pass
    content = re.sub(r'^(\s*)if (.+): (return|continue|break|pass)$', r'\1if \2:\n\1    \3', content, flags=re.MULTILINE)

    # Fix try: stmt
    content = re.sub(r'^(\s*)try: (.+)$', r'\1try:\n\1    \2', content, flags=re.MULTILINE)

    # Fix except Exc: stmt
    content = re.sub(r'^(\s*)except (.+): (.+)$', r'\1except \2:\n\1    \3', content, flags=re.MULTILINE)

    # Fix except: pass
    content = content.replace('except: pass', 'except Exception:\n            pass')

    # Fix semicolon
    # content = re.sub(r'; ', r'\n', content) # Too dangerous generally

    return content

for path in ['memex_next/ui/app.py', 'memex_next/ui/editor.py', 'memex_next/ui/search.py']:
    with open(path, 'r') as f:
        content = f.read()
    content = fix_e701_e702(content)
    # Specific safe semicolon replacements
    if 'search.py' in path:
        content = content.replace('if err: import tkinter.messagebox as mb; mb.showerror("AI", str(err))',
                                  'if err:\n                        import tkinter.messagebox as mb\n                        mb.showerror("AI", str(err))')
        content = content.replace('else: self.master.show_toast(f"Tags IA terminés ({res} éléments)"); self.refresh()',
                                  'else:\n                        self.master.show_toast(f"Tags IA terminés ({res} éléments)")\n                        self.refresh()')
        content = content.replace('else: self.master.show_toast(f"Catégories IA terminées ({res} éléments)"); self.refresh()',
                                  'else:\n                        self.master.show_toast(f"Catégories IA terminées ({res} éléments)")\n                        self.refresh()')
        content = content.replace('else: self.master.show_toast(f"IA complète terminée ({res} éléments)"); self.refresh()',
                                  'else:\n                        self.master.show_toast(f"IA complète terminée ({res} éléments)")\n                        self.refresh()')

    with open(path, 'w') as f:
        f.write(content)
