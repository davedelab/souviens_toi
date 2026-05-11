import re
path = 'memex_next/ui/search.py'
with open(path, 'r') as f:
    content = f.read()

content = content.replace('from ..config import load_config, save_config', 'from ..config import load_config, save_config, SEPARATOR')
if 'ai_generate_title' not in content:
    content = content.replace('from ..ai import ai_generate_tags, ai_generate_categories', 'from ..ai import ai_generate_tags, ai_generate_categories, ai_generate_title')

# Fix E701/E702/E722
content = content.replace('if not self.master.paused: self.master.toggle_pause()', 'if not self.master.paused:\n            self.master.toggle_pause()')
content = content.replace('if where: sql += " WHERE " + " AND ".join(where)', 'if where:\n            sql += " WHERE " + " AND ".join(where)')
content = content.replace('for w in self.tags_filter_frame.winfo_children(): w.destroy()', 'for w in self.tags_filter_frame.winfo_children():\n            w.destroy()')
content = content.replace('if tag: all_tags.add(tag)', 'if tag:\n                    all_tags.add(tag)')
content = content.replace('for w in self.cats_filter_frame.winfo_children(): w.destroy()', 'for w in self.cats_filter_frame.winfo_children():\n            w.destroy()')
content = content.replace('if tag in self.active_tag_filters: self.active_tag_filters.remove(tag)', 'if tag in self.active_tag_filters:\n            self.active_tag_filters.remove(tag)')
content = content.replace('if cat in self.active_category_filters: self.active_category_filters.remove(cat)', 'if cat in self.active_category_filters:\n            self.active_category_filters.remove(cat)')
content = content.replace('def clear_tag_filters(self): self.active_tag_filters.clear(); self.refresh()', 'def clear_tag_filters(self):\n        self.active_tag_filters.clear()\n        self.refresh()')
content = content.replace('def clear_category_filters(self): self.active_category_filters.clear(); self.refresh()', 'def clear_category_filters(self):\n        self.active_category_filters.clear()\n        self.refresh()')
content = content.replace('if not sel: return', 'if not sel:\n            return')
content = content.replace('if not row: continue', 'if not row:\n                    continue')
content = content.replace('if not paths: return', 'if not paths:\n            return')
content = content.replace('if text:', 'if text:\n                        ') # need to be careful with indentation
# Re-do search.py poll_ui properly
poll_ui_good = """    def _poll_ui(self):
        try:
            while True:
                kind, res, err = self._uiq.get_nowait()
                if kind == 'ai_tags_done':
                    if err:
                        import tkinter.messagebox as mb
                        mb.showerror("AI", str(err))
                    else:
                        self.master.show_toast(f"Tags IA terminés ({res} éléments)")
                        self.refresh()
                elif kind == 'ai_cats_done':
                    if err:
                        import tkinter.messagebox as mb
                        mb.showerror("AI", str(err))
                    else:
                        self.master.show_toast(f"Catégories IA terminées ({res} éléments)")
                        self.refresh()
                elif kind == 'ai_all_done':
                    if err:
                        import tkinter.messagebox as mb
                        mb.showerror("AI", str(err))
                    else:
                        self.master.show_toast(f"IA complète terminée ({res} éléments)")
                        self.refresh()
        except queue.Empty:
            pass
        self.after(400, self._poll_ui)"""

import re
content = re.sub(r'    def _poll_ui\(self\):.*?self\.after\(400, self\._poll_ui\)', poll_ui_good, content, flags=re.DOTALL)

with open(path, 'w') as f:
    f.write(content)
