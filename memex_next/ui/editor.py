### memex_next/ui/editor.py
import tkinter as tk, tkinter.ttk as ttk, tkinter.scrolledtext as st, tkinter.filedialog as fd, tkinter.simpledialog as sd, tkinter.messagebox as mb
import pathlib, datetime as dt, sqlite3, hashlib, mimetypes, os, tempfile, webbrowser
from typing import Optional, Dict, Any
from ..db import create_conn
from ..config import load_config, save_config
from ..ai import ai_generate_tags, ai_generate_categories, ai_generate_title
from ..services.export import clip_to_markdown
from .widgets import Tooltip

try:
    import markdown as _markdown
except Exception:
    _markdown = None
try:
    from tkhtmlview import HTMLLabel as _HTMLLabel
except Exception:
    _HTMLLabel = None
try:
    from PIL import Image, ImageTk
except Exception:
    Image = ImageTk = None

OPEN_EDITORS: Dict[int, "EditClipWindow"] = {}

class EditClipWindow(tk.Toplevel):
    def __init__(self, parent, clip_id: int, prefill: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.parent = parent
        self.clip_id = clip_id
        self.title(f"Editer clip #{self.clip_id}")
        self._fit_geometry(1020, 700)
        self.transient(parent)
        self.grab_set()
        self.protocol('WM_DELETE_WINDOW', self._close)
        self.cfg = load_config()
        self._user_cats = self.cfg.get('user_categories', [])
        self.title_var = tk.StringVar()
        self.tags_var = tk.StringVar()
        self.cat1_var = tk.StringVar()
        self.cat2_var = tk.StringVar()
        self.read_later_var = tk.BooleanVar(value=False)
        self._thumb_photos = []
        self._create_widgets()
        self._bind_shortcuts()
        if prefill: self._apply_prefill(prefill)
        OPEN_EDITORS[self.clip_id] = self
        self._load()
        self._reload_thumbnails()
        self._load_attachments_list()
        self._select_default_tab()

    def _fit_geometry(self, desired_w: int, desired_h: int) -> None:
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        width = min(desired_w, max(screen_w - 60, 400))
        height = min(desired_h, max(screen_h - 80, 300))
        self.geometry(f"{width}x{height}")
        self.resizable(True, True)

    def _create_widgets(self):
        top = ttk.Frame(self)
        top.pack(fill='both', expand=True, padx=8, pady=8)

        # Ligne titre
        row1 = ttk.Frame(top)
        row1.pack(fill='x', pady=(0,6))
        ttk.Label(row1, text="Titre", width=12).pack(side='left')
        self.title_entry = ttk.Entry(row1, textvariable=self.title_var)
        self.title_entry.pack(side='left', fill='x', expand=True)
        ttk.Button(row1, text="AI", width=4, command=self._ai_title).pack(side='left', padx=4)
        ttk.Button(row1, text="IA Tout", command=self._ai_all).pack(side='left')

        # Tags
        row2 = ttk.Frame(top)
        row2.pack(fill='x', pady=(0,6))
        ttk.Label(row2, text="Tags", width=12).pack(side='left')
        self.tags_entry = ttk.Entry(row2, textvariable=self.tags_var)
        self.tags_entry.pack(side='left', fill='x', expand=True)
        ttk.Button(row2, text="AI", width=4, command=self._ai_tags).pack(side='left', padx=4)

        # Catégories
        row3 = ttk.Frame(top)
        row3.pack(fill='x', pady=(0,6))
        ttk.Label(row3, text="Catégories", width=12).pack(side='left')
        self.cat1_cb = ttk.Combobox(row3, values=self._user_cats, textvariable=self.cat1_var, state='readonly')
        self.cat2_cb = ttk.Combobox(row3, values=self._user_cats, textvariable=self.cat2_var, state='readonly')
        self.cat1_cb.pack(side='left', fill='x', expand=True)
        self.cat2_cb.pack(side='left', fill='x', expand=True, padx=(6,0))
        ttk.Button(row3, text="AI", width=4, command=self._ai_categories).pack(side='left', padx=4)

        # Check read later
        row4 = ttk.Frame(top)
        row4.pack(fill='x', pady=(0,6))
        ttk.Checkbutton(row4, text="A lire plus tard", variable=self.read_later_var).pack(anchor='w')

        # Toolbar markdown
        toolbar = ttk.Frame(top)
        toolbar.pack(fill='x', pady=(0,6))
        def btn(txt, tip, cmd, w=4, bg="#374151"):
            b = tk.Button(toolbar, text=txt, width=w, command=cmd, bg=bg, fg='white', activebackground='#111827', relief='raised', bd=1)
            b.pack(side='left', padx=2)
            Tooltip(b, tip)
            return b
        btn("B", "Gras (Ctrl+B)", lambda: self._md_bold(), w=3, bg="#2563eb")
        btn("I", "Italique (Ctrl+I)", lambda: self._md_italic(), w=3, bg="#0ea5e9")
        btn("Link", "Lien (Ctrl+K)", lambda: self._md_link(), w=5, bg="#22c55e")
        btn("`", "Code inline", lambda: self._md_code_inline(), w=3)
        btn("```", "Bloc de code", lambda: self._md_code_block(), w=5)
        btn("H1", "H1", lambda: self._md_h1(), w=3, bg="#fbbf24")
        btn("H2", "H2", lambda: self._md_h2(), w=3, bg="#f59e0b")
        btn("H3", "H3", lambda: self._md_h3(), w=3, bg="#d97706")
        btn("â€¢", "Liste", lambda: self._md_bullet(), w=3, bg="#8b5cf6")
        btn(">", "Citation", lambda: self._md_quote(), w=3, bg="#ef4444")
        btn("HR", "Ligne horizontale", lambda: self._md_hr(), w=3, bg="#10b981")
        btn("Undo", "Annuler", lambda: self._undo_editor(), w=6)
        btn("Redo", "Rétablir", lambda: self._redo_editor(), w=6)

        # Editor
        mid = ttk.Frame(top)
        mid.pack(fill='both', expand=True)
        left = ttk.Frame(mid)
        left.pack(side='left', fill='both', expand=True)
        right = ttk.Frame(mid, width=280)
        right.pack(side='right', fill='y')

        self.editor = st.ScrolledText(left, wrap='word', undo=True, autoseparators=True, maxundo=1000)
        self.editor.pack(fill='both', expand=True)

        # Notebook droite
        self._nb_right = ttk.Notebook(right)
        self._nb_right.pack(fill='both', expand=True)
        self._tab_images = ttk.Frame(self._nb_right)
        self._nb_right.add(self._tab_images, text='Images')
        self._thumb_canvas = tk.Canvas(self._tab_images, width=260, height=520, highlightthickness=0)
        self._thumb_scroll = ttk.Scrollbar(self._tab_images, orient='vertical', command=self._thumb_canvas.yview)
        self._thumb_container = ttk.Frame(self._thumb_canvas)
        self._thumb_container.bind('<Configure>', lambda e: self._thumb_canvas.configure(scrollregion=self._thumb_canvas.bbox('all')))
        self._thumb_canvas.create_window((0, 0), window=self._thumb_container, anchor='nw')
        self._thumb_canvas.configure(yscrollcommand=self._thumb_scroll.set)
        self._thumb_canvas.pack(side='left', fill='both', expand=True)
        self._thumb_scroll.pack(side='right', fill='y')

        self._tab_attach = ttk.Frame(self._nb_right)
        self._nb_right.add(self._tab_attach, text='Pièces jointes')
        self._attach_list = tk.Listbox(self._tab_attach, height=8)
        self._attach_list.pack(fill='both', expand=True, padx=0, pady=(4,2))
        af = ttk.Frame(self._tab_attach)
        af.pack(fill='x', pady=(0,4))
        ttk.Button(af, text="Ouvrir", command=self._open_attachment_selected).pack(side='left', expand=True, fill='x')
        ttk.Button(af, text="Exporter", command=self._export_attachment_selected).pack(side='left', expand=True, fill='x', padx=2)
        ttk.Button(af, text="Supprimer", command=self._delete_attachment_selected).pack(side='left', expand=True, fill='x')
        ttk.Button(self._tab_attach, text="Joindre fichier", command=self._attach_files_to_current_clip).pack(fill='x', padx=0, pady=(0,6))

        # Boutons bas
        btn_frame = ttk.Frame(top)
        btn_frame.pack(fill='x', pady=8)
        ttk.Button(btn_frame, text="Supprimer", command=self._delete).pack(side='left')
        ttk.Button(btn_frame, text="Prévisualiser MD", command=self._preview_md).pack(side='left', padx=(8,2))
        ttk.Button(btn_frame, text="Aperçu intégré", command=self._preview_md_embedded).pack(side='left')
        ttk.Button(btn_frame, text="Enregistrer", command=self._save).pack(side='right')
        ttk.Button(btn_frame, text="Fermer", command=self._close).pack(side='right', padx=6)

    def _bind_shortcuts(self):
        for keys, func in (('<Control-s>', lambda e: self._save()), ('<Escape>', lambda e: self._close()),
                           ('<Control-b>', lambda e: (self._md_bold(), 'break')), ('<Control-i>', lambda e: (self._md_italic(), 'break')),
                           ('<Control-k>', lambda e: (self._md_link(), 'break')), ('<Control-z>', lambda e: (self._undo_editor(), 'break')),
                           ('<Control-y>', lambda e: (self._redo_editor(), 'break')), ('<Control-1>', lambda e: (self._md_h1(), 'break')),
                           ('<Control-2>', lambda e: (self._md_h2(), 'break')), ('<Control-3>', lambda e: (self._md_h3(), 'break'))):
            self.bind(keys, func)

    def _apply_prefill(self, prefill: Dict[str, Any]):
        self.title_var.set(prefill.get('title', ''))
        self.tags_var.set(prefill.get('tags', ''))
        self.editor.delete('1.0', 'end')
        self.editor.insert('1.0', prefill.get('raw_text', ''))
        parts = [p.strip() for p in (prefill.get('categories') or '').split(',') if p.strip()]
        self.cat1_var.set(parts[0] if len(parts) > 0 else '')
        self.cat2_var.set(parts[1] if len(parts) > 1 else '')
        self.read_later_var.set(bool(int(prefill.get('read_later') or 0)))

    def _select_default_tab(self):
        if not self._has_images and self._has_pdfs:
            try: self._nb_right.select(self._tab_attach)
            except Exception: pass

    def _load(self):
        conn = create_conn()
        row = conn.execute("SELECT title, raw_text, tags, categories, read_later FROM clips WHERE id=?", (self.clip_id,)).fetchone()
        conn.close()
        if not row: return
        title, raw, tags, cats, read_later = row
        self.title_var.set(title or '')
        self.tags_var.set(tags or '')
        self.editor.delete('1.0', 'end')
        self.editor.insert('1.0', raw or '')
        parts = [p.strip() for p in (cats or '').split(',') if p.strip()]
        self.cat1_var.set(parts[0] if len(parts) > 0 else '')
        self.cat2_var.set(parts[1] if len(parts) > 1 else '')
        self.read_later_var.set(bool(read_later))

    def _save(self):
        title = self.title_var.get().strip()
        tags = self.tags_var.get().strip()
        raw = self.editor.get('1.0', 'end').strip()
        cats = ', '.join([p for p in (self.cat1_var.get(), self.cat2_var.get()) if p.strip()])
        read_later = 1 if self.read_later_var.get() else 0
        summary = (raw[:150] + '...') if raw else ''
        conn = create_conn()
        conn.execute(
            "UPDATE clips SET title=?, tags=?, raw_text=?, categories=?, read_later=?, summary=? WHERE id=?",
            (title, tags, raw, cats, read_later, summary, self.clip_id)
        )
        conn.commit()
        conn.close()
        if hasattr(self.parent, 'refresh'): self.parent.refresh()
        self._toast("Clip enregistré")

    def _delete(self):
        if not mb.askyesno("Supprimer", "Supprimer ce clip ?"): return
        conn = create_conn()
        conn.execute("DELETE FROM clips WHERE id=?", (self.clip_id,))
        conn.commit()
        conn.close()
        if hasattr(self.parent, 'refresh'): self.parent.refresh()
        self._toast("Supprimé")
        self._close()

    def _close(self):
        try: self.grab_release()
        except Exception: pass
        OPEN_EDITORS.pop(self.clip_id, None)
        self.destroy()

    def _toast(self, text):
        try: self.parent.show_toast(text)
        except Exception: pass

    # ---------- Aperçu ----------
    def _preview_md(self):
        text = self.editor.get('1.0', 'end')
        html_body = _markdown.markdown(text, extensions=['extra','sane_lists','nl2br']) if _markdown else f"<pre>{text}</pre>"
        html_doc = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<style>body{max-width:860px;margin:40px auto;font-family:Segoe UI,Arial,sans-serif;line-height:1.6}"
            "pre,code{background:#f3f4f6;padding:4px;border-radius:4px} h1,h2,h3{margin-top:1.2em}</style>"
            "</head><body>" + html_body + "</body></html>"
        )
        fd, path = tempfile.mkstemp(suffix='.html')
        pathlib.Path(fd).write_text(html_doc, encoding='utf-8')
        webbrowser.open('file://' + str(pathlib.Path(path).absolute()))

    def _preview_md_embedded(self):
        text = self.editor.get('1.0', 'end')
        html_body = _markdown.markdown(text, extensions=['extra','sane_lists','nl2br']) if _markdown else f"<pre>{text}</pre>"
        win = tk.Toplevel(self)
        win.title("Aperçu Markdown (intégré)")
        win.geometry("900x700")
        if _HTMLLabel:
            html_container = _HTMLLabel(win, html=f"<div style='font-family:Segoe UI,Arial,sans-serif;line-height:1.6'>{html_body}</div>")
            html_container.pack(fill='both', expand=True)
        else:
            txt = st.ScrolledText(win, wrap='word')
            txt.pack(fill='both', expand=True)
            txt.insert('1.0', html_body)
            txt.configure(state='disabled')

    # ---------- markdown ----------
    def _sel_range(self):
        try: return self.editor.index('sel.first'), self.editor.index('sel.last')
        except tk.TclError: return None, None

    def _md_wrap(self, left, right, placeholder=''):
        start, end = self._sel_range()
        if start and end:
            text = self.editor.get(start, end)
            self.editor.delete(start, end)
            self.editor.insert(start, f"{left}{text}{right}")
            self.editor.tag_add('sel', start, f"{start}+{len(left)+len(text)+len(right)}c")
        else:
            idx = self.editor.index('insert')
            self.editor.insert(idx, f"{left}{placeholder}{right}")

    def _md_prefix_lines(self, prefix):
        start, end = self._sel_range()
        if not start or not end:
            line = self.editor.index('insert linestart')
            self.editor.insert(line, prefix)
            return
        cur = self.editor.index(start + ' linestart')
        last = self.editor.index(end + ' lineend')
        while self.editor.compare(cur, '<=', last):
            self.editor.insert(cur, prefix)
            cur = self.editor.index(cur + ' +1line')

    def _md_bold(self): self._md_wrap('**', '**', 'texte')
    def _md_italic(self): self._md_wrap('*', '*', 'texte')
    def _md_code_inline(self): self._md_wrap('`', '`', 'code')
    def _md_code_block(self):
        start, end = self._sel_range()
        if not start or not end:
            idx = self.editor.index('insert')
            self.editor.insert(idx, "\n```\n\n```\n")
            return
        text = self.editor.get(start, end)
        self.editor.delete(start, end)
        self.editor.insert(start, f"```\n{text}\n```\n")
    def _md_h1(self): self._md_prefix_lines('# ')
    def _md_h2(self): self._md_prefix_lines('## ')
    def _md_h3(self): self._md_prefix_lines('### ')
    def _md_bullet(self): self._md_prefix_lines('- ')
    def _md_quote(self): self._md_prefix_lines('> ')
    def _md_hr(self):
        idx = self.editor.index('insert')
        self.editor.insert(idx, "\n---\n")
    def _md_link(self):
        start, end = self._sel_range()
        txt = ''
        if start and end: txt = self.editor.get(start, end)
        url = sd.askstring("Lien", "URL:")
        if not url: return
        label = txt or sd.askstring("Lien", "Texte du lien:", initialvalue=url) or url
        if start and end:
            self.editor.delete(start, end)
            self.editor.insert(start, f"[{label}]({url})")
        else:
            idx = self.editor.index('insert')
            self.editor.insert(idx, f"[{label}]({url})")

    def _undo_editor(self):
        try: self.editor.edit_undo()
        except tk.TclError: pass
    def _redo_editor(self):
        try: self.editor.edit_redo()
        except tk.TclError: pass

    # ---------- IA ----------
    def _ai_tags(self):
        text = self.editor.get('1.0', 'end').strip()
        if not text: mb.showinfo("IA", "Aucun texte à analyser"); return
        cfg = load_config()
        lang = cfg.get('ai_lang', 'fr')
        count = int(cfg.get('ai_tag_count', 5))
        def work():
            return ai_generate_tags(text, lang=lang, count=count)
        def done(res, err):
            if err: mb.showerror("IA", str(err)); return
            existing = [p.strip() for p in (self.tags_var.get() or '').replace(';', ',').split(',') if p.strip()]
            merged = list(dict.fromkeys(existing + (res or [])))
            self.tags_var.set(', '.join(merged))
            self._toast("Tags IA proposés")
        from ..services.async_worker import runner
        runner.submit(work, cb=lambda r,e: self.after(0, done, r, e))

    def _ai_categories(self):
        text = self.editor.get('1.0', 'end').strip()
        if not text: mb.showinfo("IA", "Aucun texte à analyser"); return
        if not self._user_cats: mb.showinfo("IA", "Aucune catégorie définie (Options > Catégories)"); return
        def work():
            return ai_generate_categories(text, user_cats=self._user_cats, lang=self.cfg.get('ai_lang','fr'), max_n=2)
        def done(res, err):
            if err: mb.showerror("IA", str(err)); return
            res = res or []
            self.cat1_var.set(res[0] if len(res) > 0 else '')
            self.cat2_var.set(res[1] if len(res) > 1 else '')
            self._toast("Catégories IA proposées")
        from ..services.async_worker import runner
        runner.submit(work, cb=lambda r,e: self.after(0, done, r, e))

    def _ai_title(self):
        text = self.editor.get('1.0', 'end').strip()
        if not text: mb.showinfo("IA", "Aucun texte à analyser"); return
        cfg = load_config()
        lang = cfg.get('ai_lang', 'fr')
        max_len = int(cfg.get('ai_title_max_len', 80))
        def work():
            return ai_generate_title(text, lang=lang, max_len=max_len)
        def done(res, err):
            if err: mb.showerror("IA", str(err)); return
            if res: self.title_var.set(res); self._toast("Titre IA appliqué")
        from ..services.async_worker import runner
        runner.submit(work, cb=lambda r,e: self.after(0, done, r, e))

    def _ai_all(self):
        text = self.editor.get('1.0', 'end').strip()
        if not text: mb.showinfo("IA", "Aucun texte à analyser"); return
        cfg = load_config()
        lang = cfg.get('ai_lang', 'fr')
        max_len = int(cfg.get('ai_title_max_len', 80))
        user_cats = cfg.get('user_categories', [])
        count = int(cfg.get('ai_tag_count', 5))
        def work():
            title = ai_generate_title(text, lang=lang, max_len=max_len)
            tags  = ai_generate_tags(text, lang=lang, count=count)
            cats  = ai_generate_categories(text, user_cats=user_cats, lang=lang, max_n=2) if user_cats else []
            return {"title": title, "tags": tags, "categories": cats}
        def done(res, err):
            if err: mb.showerror("IA", str(err)); return
            if not res: return
            if res.get('title'): self.title_var.set(res['title'])
            if res.get('tags') is not None:
                existing = [p.strip() for p in (self.tags_var.get() or '').replace(';', ',').split(',') if p.strip()]
                merged = list(dict.fromkeys(existing + (res['tags'] or [])))
                self.tags_var.set(', '.join(merged))
            parts = [p.strip() for p in (res.get('categories') or []) if p.strip()]
            self.cat1_var.set(parts[0] if len(parts) > 0 else '')
            self.cat2_var.set(parts[1] if len(parts) > 1 else '')
            self._toast("Titre, tags et Catégories IA appliqués")
        from ..services.async_worker import runner
        runner.submit(work, cb=lambda r,e: self.after(0, done, r, e))

    # ---------- Pièces jointes ----------
    def _attach_files_to_current_clip(self):
        paths = fd.askopenfilenames(
            filetypes=[["PDF","*.pdf"],["Images","*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp"],
                       ["Documents","*.txt;*.md;*.docx"],["Tous","*.*"]]
        )
        if not paths: return
        added = 0
        for p in paths:
            try:
                data = pathlib.Path(p).read_bytes()
                sha = hashlib.sha256(data).hexdigest()
                mime = mimetypes.guess_type(p)[0] or 'application/octet-stream'
                title = pathlib.Path(p).name
                conn = create_conn()
                conn.execute("INSERT OR IGNORE INTO files(clip_id, filename, mime, size, sha256, data) VALUES (?,?,?,?,?,?)",
                             (self.clip_id, title, mime, len(data), sha, data))
                conn.commit()
                conn.close()

                def work(mime=mime, blob=data):
                    from ..ocr import extract_text_from_blob
                    text = extract_text_from_blob(blob, mime)
                    if text:
                        conn = create_conn()
                        row = conn.execute("SELECT raw_text FROM clips WHERE id=?", (self.clip_id,)).fetchone()
                        current = (row[0] or '') if row else ''
                        sep = ("\n" + SEPARATOR + "\n") if current else ''
                        conn.execute("UPDATE clips SET raw_text=?, summary=? WHERE id=?",
                                     (current + sep + text, (current + sep + text)[:150] + '...', self.clip_id))
                        conn.commit()
                        conn.close()
                        return True
                    return False
                def done(res, err):
                    self._toast("Fichier joint" + (" et indexé" if res else ''))
                    self._load_attachments_list()
                    self._reload_thumbnails()
                from ..services.async_worker import runner
                runner.submit(work, cb=lambda r,e: self.after(0, done, r, e))
                added += 1
            except Exception as e:
                mb.showerror("Import", f"Echec import {pathlib.Path(p).name}: {e}")
        if added: self._toast(f"{added} fichier(s) joint(s)")

    def _reload_thumbnails(self):
        for w in self._thumb_container.winfo_children(): w.destroy()
        self._thumb_photos.clear()
        self._has_images = False
        self._has_pdfs = False
        conn = create_conn()
        rows = conn.execute("SELECT id, filename, mime, data FROM files WHERE clip_id=? ORDER BY id DESC", (self.clip_id,)).fetchall()
        conn.close()
        for fid, fn, mime, blob in rows:
            if mime and mime.startswith('image/') and Image is not None and ImageTk is not None:
                try:
                    img = Image.open(BytesIO(blob))
                    img.thumbnail((240, 180))
                    ph = ImageTk.PhotoImage(img)
                    lbl = tk.Label(self._thumb_container, image=ph, cursor='hand2')
                    lbl.image = ph
                    lbl.pack(fill='x', pady=4)
                    lbl.bind('<Button-1>', lambda e, b=blob, t=fn: self._open_image_preview(b, t))
                    self._thumb_photos.append(ph)
                    self._has_images = True
                except Exception: continue
            elif mime == 'application/pdf':
                card = ttk.Frame(self._thumb_container, relief='ridge', borderwidth=1)
                card.pack(fill='x', pady=4)
                ttk.Label(card, text=fn or f"PDF #{fid}").pack(side='top', anchor='w', padx=4, pady=(4,0))
                btns = ttk.Frame(card)
                btns.pack(fill='x', pady=(2,4))
                ttk.Button(btns, text="Ouvrir", command=lambda i=fid: self._open_attachment_by_id(i)).pack(side='left')
                ttk.Button(btns, text="Exporter", command=lambda i=fid: self._export_attachment_by_id(i)).pack(side='left', padx=4)
                ttk.Button(btns, text="Supprimer", command=lambda i=fid: self._delete_attachment_by_id(i)).pack(side='left')
                self._has_pdfs = True

    def _load_attachments_list(self):
        self._attach_list.delete(0, 'end')
        conn = create_conn()
        rows = conn.execute("SELECT id, filename, size, mime FROM files WHERE clip_id=? ORDER BY id DESC", (self.clip_id,)).fetchall()
        conn.close()
        for fid, fn, sz, mime in rows:
            self._attach_list.insert('end', f"{fid} - {fn} ({sz or 0} o) [{mime}]")

    def _selected_attachment_id(self):
        try:
            sel = self._attach_list.curselection()
            if not sel: return None
            return int(self._attach_list.get(sel[0]).split(' - ', 1)[0])
        except Exception: return None

    def _open_attachment_selected(self):
        fid = self._selected_attachment_id()
        if fid is None: return
        self._open_attachment_by_id(fid)

    def _export_attachment_selected(self):
        fid = self._selected_attachment_id()
        if fid is None: return
        self._export_attachment_by_id(fid)

    def _delete_attachment_selected(self):
        fid = self._selected_attachment_id()
        if fid is None: return
        self._delete_attachment_by_id(fid)

    def _open_attachment_by_id(self, fid):
        conn = create_conn()
        row = conn.execute("SELECT filename, data, mime FROM files WHERE id=?", (fid,)).fetchone()
        conn.close()
        if not row: return
        fn, data, mime = row
        ext = pathlib.Path(fn).suffix or '.' + (mime.split('/')[-1] if mime else 'bin')
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(data)
            tmp.flush()
            try: os.startfile(tmp.name)
            except Exception: mb.showinfo("Ouvrir", f"Fichier enregistré: {tmp.name}")

    def _export_attachment_by_id(self, fid):
        conn = create_conn()
        row = conn.execute("SELECT filename, data FROM files WHERE id=?", (fid,)).fetchone()
        conn.close()
        if not row: return
        fn, data = row
        path = fd.asksaveasfilename(initialfile=fn, defaultextension=pathlib.Path(fn).suffix or '.pdf')
        if not path: return
        pathlib.Path(path).write_bytes(data)
        self._toast("Fichier exporté")

    def _delete_attachment_by_id(self, fid):
        if not mb.askyesno("Supprimer", "Supprimer cette pièce jointe ?"): return
        conn = create_conn()
        conn.execute("DELETE FROM files WHERE id=?", (fid,))
        conn.commit()
        conn.close()
        self._load_attachments_list()
        self._reload_thumbnails()

    def _open_image_preview(self, blob, title):
        if Image is None or ImageTk is None: return
        try:
            img = Image.open(BytesIO(blob))
            win = tk.Toplevel(self)
            win.title(title)
            win.geometry("900x700")
            canvas = tk.Canvas(win, bg='#111')
            canvas.pack(fill='both', expand=True)
            state = {"ph": None}
            def render():
                try:
                    w = canvas.winfo_width() or 900
                    h = canvas.winfo_height() or 700
                    im = img.copy()
                    im.thumbnail((w-20, h-20))
                    ph = ImageTk.PhotoImage(im)
                    state["ph"] = ph
                    canvas.delete('all')
                    canvas.create_image(w//2, h//2, image=ph, anchor='center')
                except Exception: pass
            canvas.bind('<Configure>', lambda e: render())
            render()
        except Exception: pass
