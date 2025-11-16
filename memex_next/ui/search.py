### memex_next/ui/search.py
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.scrolledtext as scrolledtext
import tkinter.filedialog as fd
import tkinter.messagebox as mb
import tkinter.simpledialog as sd
import datetime as dt
import json
import pathlib
import queue
from typing import List, Dict, Any
from ..db import create_conn
from ..services.export import export_selected_md, export_json
from ..ai import ai_generate_tags, ai_generate_categories
from ..config import load_config, save_config
from .editor import EditClipWindow, OPEN_EDITORS
from ..services.async_worker import runner

class SearchWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("Recherche Souviens-toi")
        self.geometry("1200x700")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        if not self.master.paused: self.master.toggle_pause()

        self.period_var = tk.StringVar(value="")
        self.query_var = tk.StringVar()
        self.query_var.trace_add("write", self.refresh)
        self.active_tag_filters = set()
        self.active_category_filters = set()
        self.read_later_only = tk.BooleanVar(value=False)
        self._sort_col = 'date'
        self._sort_desc = True
        self._uiq = queue.Queue()
        self.build_ui()
        self.bind("<Control-s>", lambda e: self.open_clip_editor())
        self.bind("<Delete>", lambda e: self.bulk_delete_selected())
        self.bind("<Return>", lambda e: self.refresh())
        self.after(200, self._poll_ui)
        self.clear_all_filters()
        self.refresh()

    def build_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Gauche : recherche + résultats
        left = ttk.Frame(main_frame)
        left.pack(side='left', fill='both', expand=True, padx=(0,5))

        search_frame = ttk.Frame(left)
        search_frame.pack(fill='x', pady=(0,5))
        ttk.Entry(search_frame, textvariable=self.query_var, font=("Segoe", 14)).pack(side='left', fill='x', expand=True)
        ttk.Button(search_frame, text="Rechercher", command=self.refresh).pack(side='left', padx=2)

        period_frame = ttk.Frame(left)
        period_frame.pack(fill='x', pady=(0,5))
        for label, days in [("Tout", ""), ("Hier", "1"), ("Semaine", "7"), ("Quinzaine", "15"), ("Mois", "30")]:
            ttk.Radiobutton(period_frame, text=label, variable=self.period_var, value=days, command=self.refresh).pack(side='left', padx=3)
        ttk.Checkbutton(left, text="À lire plus tard", variable=self.read_later_only, command=self.refresh).pack(anchor='w', pady=(0,5))

        # Filtres tags
        self.tags_filter_frame = ttk.Frame(left)
        self.tags_filter_frame.pack(fill='x', pady=(0,5))
        ttk.Button(left, text="Effacer filtres", command=self.clear_tag_filters).pack(anchor='w', pady=(0,5))

        # Filtres catégories
        self.cats_filter_frame = ttk.Frame(left)
        self.cats_filter_frame.pack(fill='x', pady=(0,5))
        ttk.Button(left, text="Effacer filtres catégories", command=self.clear_category_filters).pack(anchor='w', pady=(0,5))

        # Tree
        cols = ("date", "title", "categories", "tags")
        self.tree = ttk.Treeview(left, columns=cols, show='headings', selectmode='extended')
        for c in cols:
            self.tree.heading(c, text=c.capitalize(), command=lambda col=c: self.sort_by(col))
            self.tree.column(c, width=100 if c == 'date' else 250 if c == 'title' else 160)
        self.tree.pack(fill='both', expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<ButtonRelease-1>", lambda e: self.after(1, self.on_tree_select))
        self.tree.bind("<Double-1>", self.open_clip_editor)
        self._tree_menu = tk.Menu(self, tearoff=0)
        self._build_context_menu()
        self.tree.bind("<Button-3>", self._on_tree_right_click)

        # Centre : aperçu
        center = ttk.Frame(main_frame)
        center.pack(side='left', fill='both', expand=True)
        meta = ttk.Frame(center)
        meta.pack(fill='x')
        self.prev_title = ttk.Label(meta, text="", font=("Segoe UI", 11, 'bold'))
        self.prev_title.pack(anchor='w')
        self.prev_info = ttk.Label(meta, text="", foreground="#6b7280")
        self.prev_info.pack(anchor='w')
        self.preview = scrolledtext.ScrolledText(center, wrap='word', height=10, state='disabled')
        self.preview.pack(fill='both', expand=True, pady=(4,0))

        # Droite : actions
        right = ttk.Frame(main_frame)
        right.pack(side='right', fill='y', padx=(5,0))
        ttk.Label(right, text="Actions").pack(anchor='w')
        ttk.Button(right, text="Ouvrir", command=self.open_clip_editor).pack(fill='x', pady=2)
        ttk.Button(right, text="Supprimer", command=self.delete_clip).pack(fill='x', pady=2)
        ttk.Button(right, text="Supprimer sélection", command=self.bulk_delete_selected).pack(fill='x', pady=2)

        ttk.Label(right, text="IA").pack(anchor='w', pady=(8,0))
        ttk.Button(right, text="Tags manquants (IA)", command=self.ai_tags_missing).pack(fill='x', pady=2)
        ttk.Button(right, text="Traiter non traités (IA)", command=self.ai_process_untagged).pack(fill='x', pady=2)
        ttk.Button(right, text="Catégories (sélection)", command=self.ai_cats_selected).pack(fill='x', pady=2)
        ttk.Button(right, text="Catégories manquantes", command=self.ai_cats_missing).pack(fill='x', pady=2)
        ttk.Button(right, text="Tout (sélection)", command=self.ai_all_selected).pack(fill='x', pady=6)

        ttk.Label(right, text="Pièces jointes").pack(anchor='w', pady=(8,0))
        ttk.Button(right, text="Joindre fichier au clip", command=self.attach_files_to_selected_clip).pack(fill='x', pady=2)

        ttk.Label(right, text="Export/Import").pack(anchor='w', pady=(8,0))
        ttk.Button(right, text="Export MD (sélection)", command=self.export_selected_md).pack(fill='x', pady=2)
        ttk.Button(right, text="Export MD (tout)", command=self.export_all_md).pack(fill='x', pady=2)
        ttk.Button(right, text="Export JSON (sélection)", command=self.export_selected_json).pack(fill='x', pady=2)
        ttk.Button(right, text="Export JSON (tout)", command=self.export_all_json).pack(fill='x', pady=2)
        ttk.Button(right, text="Importer JSON", command=self.import_json).pack(fill='x', pady=2)

    # ---------- actions ----------
    def refresh(self, *args):
        query = self.query_var.get().strip()
        period = self.period_var.get()
        prev_selected = set(self.tree.selection())
        conn = create_conn()
        if not query and not period:
            rows = conn.execute("SELECT * FROM clips ORDER BY ts DESC").fetchall()
        else:
            rows = self._search_sql(conn, query, period)
        # conn.close()
        clips = [dict(zip([c[0] for c in conn.execute("SELECT * FROM clips LIMIT 1").description], r)) for r in rows]
        if self.read_later_only.get():
            clips = [c for c in clips if c.get('read_later')]
        if self.active_tag_filters:
            clips = [c for c in clips if any(t.lower() in {tg.lower() for tg in self.active_tag_filters} for t in (c.get('tags') or '').replace(';',',').split(','))]
        if self.active_category_filters:
            clips = [c for c in clips if any(cat.lower() in {c2.lower() for c2 in self.active_category_filters} for cat in (c.get('categories') or '').split(','))]
        key_map = {'date': lambda r: r['ts'], 'title': lambda r: (r['title'] or '').lower(),
                   'categories': lambda r: (r.get('categories') or '').lower(), 'tags': lambda r: (r['tags'] or '').lower()}
        clips.sort(key=key_map.get(self._sort_col, key_map['date']), reverse=self._sort_desc)
        self.tree.delete(*self.tree.get_children())
        for c in clips:
            self.tree.insert('', 'end', iid=str(c['id']),
                             values=(dt.datetime.fromtimestamp(c['ts'], tz=dt.timezone.utc).strftime('%Y-%m-%d'),
                                     c['title'], c.get('categories'), c['tags']))
        to_select = [iid for iid in self.tree.get_children() if iid in prev_selected]
        if to_select: self.tree.selection_set(to_select)
        else:
            children = self.tree.get_children()
            if children: self.tree.selection_set(children[0]); self.on_tree_select()
        self.build_tag_filters()

    def _search_sql(self, conn, query, period):
        now = dt.datetime.now(dt.timezone.utc)
        params, where = [], []
        if query:
            where.append("raw_text LIKE ?")
            params.append(f"%{query}%")
        if period:
            where.append("ts >= ?")
            params.append(int((now - dt.timedelta(days=int(period))).timestamp()))
        sql = "SELECT * FROM clips"
        if where: sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY ts DESC LIMIT 500"
        cur = conn.execute(sql, params)
        return cur.fetchall()

    def build_tag_filters(self):
        for w in self.tags_filter_frame.winfo_children(): w.destroy()
        conn = create_conn()
        rows = conn.execute("SELECT tags FROM clips WHERE tags IS NOT NULL AND tags <> ''").fetchall()
        conn.close()
        all_tags = set()
        for (t,) in rows:
            for part in str(t).replace(';', ',').split(','):
                tag = part.strip()
                if tag: all_tags.add(tag)
        if not all_tags: return
        # top 20
        counts = {}
        conn = create_conn()
        for tag in all_tags:
            counts[tag] = conn.execute("SELECT COUNT(*) FROM clips WHERE tags LIKE ?", (f'%{tag}%',)).fetchone()[0]
        conn.close()
        for tag, _ in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:20]:
            btn = tk.Button(self.tags_filter_frame, text=f"{tag} ({counts[tag]})", relief='raised', bd=1, padx=4, pady=2,
                            command=lambda t=tag: self.toggle_tag_filter(t))
            btn.config(bg='#3b82f6' if tag in self.active_tag_filters else '#e5e7eb', fg='white' if tag in self.active_tag_filters else 'black')
            btn.pack(side='left', padx=2, pady=2)

    def build_category_filters(self):
        for w in self.cats_filter_frame.winfo_children(): w.destroy()
        user_cats = load_config().get('user_categories', [])
        if not user_cats: return
        counts = {}
        conn = create_conn()
        for cat in user_cats:
            counts[cat] = conn.execute("SELECT COUNT(*) FROM clips WHERE categories LIKE ?", (f"%{cat}%",)).fetchone()[0]
        conn.close()
        for cat in user_cats:
            btn = tk.Button(self.cats_filter_frame, text=f"{cat} ({counts.get(cat,0)})", relief='raised', bd=1, padx=4, pady=2,
                            command=lambda t=cat: self.toggle_category_filter(t))
            btn.config(bg='#10b981' if cat in self.active_category_filters else '#e5e7eb', fg='white' if cat in self.active_category_filters else 'black')
            btn.pack(side='left', padx=2, pady=2)

    def toggle_tag_filter(self, tag):
        if tag in self.active_tag_filters: self.active_tag_filters.remove(tag)
        else: self.active_tag_filters.add(tag)
        cfg = load_config()
        cfg['active_tag_filters'] = sorted(self.active_tag_filters)
        save_config(cfg)
        self.refresh()

    def toggle_category_filter(self, cat):
        if cat in self.active_category_filters: self.active_category_filters.remove(cat)
        else: self.active_category_filters.add(cat)
        cfg = load_config()
        cfg['active_category_filters'] = sorted(self.active_category_filters)
        save_config(cfg)
        self.refresh()

    def clear_tag_filters(self): self.active_tag_filters.clear(); self.refresh()
    def clear_category_filters(self): self.active_category_filters.clear(); self.refresh()
    def clear_all_filters(self):
        self.query_var.set("")
        self.period_var.set("")
        self.read_later_only.set(False)
        self.active_tag_filters.clear()
        self.active_category_filters.clear()
        self.refresh()

    # ---------- tree ----------
    def on_tree_select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            self.prev_title.config(text="")
            self.prev_info.config(text="")
            self.preview.configure(state='normal'); self.preview.delete('1.0','end'); self.preview.configure(state='disabled')
            return
        clip_id = int(sel[0])
        conn = create_conn()
        row = conn.execute("SELECT title, raw_text, tags, categories, ts, source FROM clips WHERE id=?", (clip_id,)).fetchone()
        conn.close()
        if not row: return
        title, raw, tags, cats, ts, source = row
        info_parts = []
        if tags: info_parts.append(f"Tags: {tags}")
        if cats: info_parts.append(f"Catégories: {cats}")
        if source: info_parts.append(f"Source: {source}")
        date_str = dt.datetime.fromtimestamp(ts or 0, tz=dt.timezone.utc).strftime('%Y-%m-%d') if ts else ''
        if date_str: info_parts.insert(0, date_str)
        self.prev_title.config(text=title or "(Sans titre)")
        self.prev_info.config(text="  ¢  ".join(info_parts))
        self.preview.configure(state='normal')
        self.preview.delete('1.0','end')
        self.preview.insert('1.0', raw or '')
        self._highlight_preview()
        self.preview.configure(state='disabled')

    def _highlight_preview(self):
        q = self.query_var.get().strip()
        self.preview.tag_delete('hl')
        if not q: return
        self.preview.tag_config('hl', background='#fde047')
        for term in q.split():
            if not term: continue
            idx = '1.0'
            while True:
                idx = self.preview.search(term, idx, nocase=True, stopindex='end')
                if not idx: break
                end = f"{idx}+{len(term)}c"
                self.preview.tag_add('hl', idx, end)
                idx = end

    # ---------- actions ----------
    def open_clip_editor(self, event=None):
        sel = self.tree.selection()
        if not sel: return
        clip_id = int(sel[0])
        EditClipWindow(self, clip_id)

    def delete_clip(self):
        sel = self.tree.selection()
        if not sel: return
        clip_id = int(sel[0])
        if not tk.messagebox.askyesno("Confirmation", "Supprimer ce clip ?"): return
        conn = create_conn()
        conn.execute("DELETE FROM clips WHERE id=?", (clip_id,))
        conn.commit()
        conn.close()
        self.refresh()

    def bulk_delete_selected(self):
        sels = self.tree.selection()
        if not sels: return
        if not tk.messagebox.askyesno("Confirmation", f"Supprimer {len(sels)} éléments ?"): return
        ids = [int(i) for i in sels]
        conn = create_conn()
        conn.executemany("DELETE FROM clips WHERE id=?", [(i,) for i in ids])
        conn.commit()
        conn.close()
        self.refresh()

    # ---------- export ----------
    def export_selected_md(self):
        sels = self.tree.selection()
        if not sels: return
        ids = [int(i) for i in sels]
        conn = create_conn()
        rows = conn.execute(f"SELECT * FROM clips WHERE id IN ({','.join('?'*len(ids))})", ids).fetchall()
        conn.close()
        clips = [dict(zip([c[0] for c in conn.execute("SELECT * FROM clips LIMIT 1").description], r)) for r in rows]
        folder = tk.filedialog.askdirectory()
        if not folder: return
        count = export_selected_md(clips, pathlib.Path(folder), load_config())
        tk.messagebox.showinfo("Export", f"{count} fichiers Markdown exportés.")

    def export_all_md(self):
        conn = create_conn()
        rows = conn.execute("SELECT * FROM clips ORDER BY ts DESC").fetchall()
        conn.close()
        clips = [dict(zip([c[0] for c in conn.execute("SELECT * FROM clips LIMIT 1").description], r)) for r in rows]
        folder = tk.filedialog.askdirectory()
        if not folder: return
        count = export_selected_md(clips, pathlib.Path(folder), load_config())
        tk.messagebox.showinfo("Export", f"{count} fichiers Markdown exportés.")

    def export_selected_json(self):
        sels = self.tree.selection()
        if not sels: return
        ids = [int(i) for i in sels]
        conn = create_conn()
        rows = conn.execute(f"SELECT * FROM clips WHERE id IN ({','.join('?'*len(ids))})", ids).fetchall()
        conn.close()
        clips = [dict(zip([c[0] for c in conn.execute("SELECT * FROM clips LIMIT 1").description], r)) for r in rows]
        path = tk.filedialog.asksaveasfilename(defaultextension=".json", filetypes=[["JSON","*.json"]])
        if not path: return
        export_json(clips, pathlib.Path(path))
        tk.messagebox.showinfo("Export", "Sélection exportée en JSON.")

    def export_all_json(self):
        conn = create_conn()
        rows = conn.execute("SELECT * FROM clips ORDER BY ts DESC").fetchall()
        conn.close()
        clips = [dict(zip([c[0] for c in conn.execute("SELECT * FROM clips LIMIT 1").description], r)) for r in rows]
        path = tk.filedialog.asksaveasfilename(defaultextension=".json", filetypes=[["JSON","*.json"]])
        if not path: return
        export_json(clips, pathlib.Path(path))
        tk.messagebox.showinfo("Export", "Base complète exportée en JSON.")

    def import_json(self):
        path = tk.filedialog.askopenfilename(filetypes=[["JSON","*.json"]])
        if not path: return
        from ..services.importer import import_json as imp
        try:
            imp(pathlib.Path(path))
            self.refresh()
            tk.messagebox.showinfo("Import", "Fichier JSON importé.")
        except Exception as e:
            tk.messagebox.showerror("Erreur", f"Import échoué: {e}")

    # ---------- IA batch ----------
    def ai_tags_missing(self):
        cfg = load_config()
        lang = cfg.get('ai_lang', 'fr')
        count = int(cfg.get('ai_tag_count', 5))
        def work():
            conn = create_conn()
            rows = conn.execute("SELECT id, raw_text FROM clips WHERE tags='' OR tags='non traitée par l IA'").fetchall()
            updated = 0
            for i, raw in rows:
                tags = ai_generate_tags(raw or '', lang=lang, count=count)
                conn.execute("UPDATE clips SET tags=? WHERE id=?", (', '.join(tags), i))
                updated += 1
            conn.commit()
            conn.close()
            return updated
        runner.submit(work, cb=lambda res, err: self._uiq.put(("ai_tags_done", res, err)))
        self.master.show_toast("Tags IA pour les non traités en arrière-plan…")

    def ai_process_untagged(self):
        cfg = load_config()
        lang = cfg.get('ai_lang', 'fr')
        count = int(cfg.get('ai_tag_count', 5))
        def work():
            conn = create_conn()
            rows = conn.execute("SELECT id, raw_text FROM clips WHERE tags LIKE ?", ("%non traitée par l IA%",)).fetchall()
            updated = 0
            for i, raw in rows:
                tags = ai_generate_tags(raw or '', lang=lang, count=count)
                conn.execute("UPDATE clips SET tags=? WHERE id=?", (', '.join(tags), i))
                updated += 1
            conn.commit()
            conn.close()
            return updated
        runner.submit(work, cb=lambda res, err: self._uiq.put(("ai_tags_done", res, err)))
        self.master.show_toast("Traitement IA des non traités…")
    def ai_tags_selected(self):
        sels = self.tree.selection()
        if not sels: return
        cfg = load_config()
        lang = cfg.get('ai_lang', 'fr')
        count = int(cfg.get('ai_tag_count', 5))
        ids = [int(i) for i in sels]
        def work():
            conn = create_conn()
            updated = 0
            for i in ids:
                row = conn.execute("SELECT raw_text, tags FROM clips WHERE id=?", (i,)).fetchone()
                if not row: continue
                raw, existing = row
                tags_ai = ai_generate_tags(raw or '', lang=lang, count=count)
                existing_list = [p.strip() for p in (existing or '').replace(';', ',').split(',') if p.strip()]
                merged = list(dict.fromkeys(existing_list + tags_ai))
                conn.execute("UPDATE clips SET tags=? WHERE id=?", (', '.join(merged), i))
                updated += 1
            conn.commit()
            conn.close()
            return updated
        from ..services.async_worker import runner
        runner.submit(work, cb=lambda res, err: self._uiq.put(("ai_tags_done", res, err)))
        self.master.show_toast("Tags IA en arrière-plan…")
    def ai_cats_selected(self):
        sels = self.tree.selection()
        if not sels: return
        cfg = load_config()
        user_cats = cfg.get('user_categories', [])
        if not user_cats:
            tk.messagebox.showinfo("IA", "Aucune catégorie définie (Options > Catégories)")
            return
        ids = [int(i) for i in sels]
        def work():
            conn = create_conn()
            updated = 0
            for i in ids:
                row = conn.execute("SELECT raw_text FROM clips WHERE id=?", (i,)).fetchone()
                if not row: continue
                cats = ai_generate_categories(row[0] or '', user_cats=user_cats, lang=cfg.get('ai_lang','fr'), max_n=2)
                conn.execute("UPDATE clips SET categories=? WHERE id=?", (', '.join(cats), i))
                updated += 1
            conn.commit()
            conn.close()
            return updated
        runner.submit(work, cb=lambda res, err: self._uiq.put(("ai_cats_done", res, err)))
        self.master.show_toast("Catégories IA en arrière-plan…")

    def ai_cats_missing(self):
        cfg = load_config()
        user_cats = cfg.get('user_categories', [])
        if not user_cats:
            tk.messagebox.showinfo("IA", "Aucune catégorie définie (Options > Catégories)")
            return
        def work():
            conn = create_conn()
            rows = conn.execute("SELECT id, raw_text FROM clips WHERE categories IS NULL OR categories='' ").fetchall()
            updated = 0
            for i, raw in rows:
                cats = ai_generate_categories(raw or '', user_cats=user_cats, lang=cfg.get('ai_lang','fr'), max_n=2)
                conn.execute("UPDATE clips SET categories=? WHERE id=?", (', '.join(cats), i))
                updated += 1
            conn.commit()
            conn.close()
            return updated
        runner.submit(work, cb=lambda res, err: self._uiq.put(("ai_cats_done", res, err)))
        self.master.show_toast("Catégories IA (manquantes)…")

    def ai_all_selected(self):
        sels = self.tree.selection()
        if not sels: return
        cfg = load_config()
        lang = cfg.get('ai_lang', 'fr')
        user_cats = cfg.get('user_categories', [])
        count = int(cfg.get('ai_tag_count', 5))
        max_len = int(cfg.get('ai_title_max_len', 80))
        ids = [int(i) for i in sels]
        def work():
            conn = create_conn()
            updated = 0
            for i in ids:
                row = conn.execute("SELECT raw_text, tags FROM clips WHERE id=?", (i,)).fetchone()
                if not row: continue
                raw, existing_tags = row
                title = ai_generate_title(raw or '', lang=lang, max_len=max_len)
                tags  = ai_generate_tags(raw or '', lang=lang, count=count)
                cats  = ai_generate_categories(raw or '', user_cats=user_cats, lang=lang, max_n=2) if user_cats else []
                existing_list = [p.strip() for p in (existing_tags or '').replace(';', ',').split(',') if p.strip()]
                merged_tags = list(dict.fromkeys(existing_list + tags))
                conn.execute(
                    "UPDATE clips SET title=COALESCE(?, title), tags=?, categories=? WHERE id=?",
                    (title, ', '.join(merged_tags), ', '.join(cats), i)
                )
                updated += 1
            conn.commit()
            conn.close()
            return updated
        runner.submit(work, cb=lambda res, err: self._uiq.put(("ai_all_done", res, err)))
        self.master.show_toast("IA (Titre+Tags+Catégories)…")

    # ---------- pièces jointes ----------
    def attach_files_to_selected_clip(self):
        sels = self.tree.selection()
        if not sels: return
        clip_id = int(sels[0])
        from tkinter import filedialog
        paths = filedialog.askopenfilenames(
            filetypes=[["PDF","*.pdf"],["Images","*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp"],["Documents","*.txt;*.md;*.docx"],["Tous","*.*"]]
        )
        if not paths: return
        import hashlib, mimetypes
        added = 0
        for p in paths:
            try:
                data = pathlib.Path(p).read_bytes()
                sha = hashlib.sha256(data).hexdigest()
                mime = mimetypes.guess_type(p)[0] or 'application/octet-stream'
                title = pathlib.Path(p).name
                conn = create_conn()
                conn.execute("INSERT OR IGNORE INTO files(clip_id, filename, mime, size, sha256, data) VALUES (?,?,?,?,?,?)",
                             (clip_id, title, mime, len(data), sha, data))
                conn.commit()
                conn.close()

                def work(clip_id=clip_id, mime=mime, blob=data):
                    from ..ocr import extract_text_from_blob
                    text = extract_text_from_blob(blob, mime)
                    if text:
                        conn = create_conn()
                        row = conn.execute("SELECT raw_text FROM clips WHERE id=?", (clip_id,)).fetchone()
                        current = (row[0] or '') if row else ''
                        sep = ("\n" + SEPARATOR + "\n") if current else ''
                        conn.execute("UPDATE clips SET raw_text=?, summary=? WHERE id=?",
                                     (current + sep + text, (current + sep + text)[:150] + '...', clip_id))
                        conn.commit()
                        conn.close()
                        return True
                    return False
                def done(res, err):
                    self.master.show_toast("Fichier joint" + (" et indexé" if res else ''))
                    self.on_tree_select()
                runner.submit(work, cb=lambda r,e: self.after(0, done, r, e))
                added += 1
            except Exception as e:
                import tkinter.messagebox as mb
                mb.showerror("Import", f"Échec import {pathlib.Path(p).name}: {e}")
        if added:
            self.master.show_toast(f"{added} fichier(s) joint(s)")

    # ---------- divers ----------
    def sort_by(self, col):
        if self._sort_col == col: self._sort_desc = not self._sort_desc
        else: self._sort_col = col; self._sort_desc = (col == 'date')
        self.refresh()

    def on_close(self):
        if self.master.paused: self.master.toggle_pause()
        cfg = load_config()
        cfg['active_tag_filters'] = sorted(self.active_tag_filters)
        cfg['active_category_filters'] = sorted(self.active_category_filters)
        cfg['filter_read_later'] = bool(self.read_later_only.get())
        save_config(cfg)
        self.destroy()

    def _poll_ui(self):
        try:
            while True:
                kind, res, err = self._uiq.get_nowait()
                if kind == 'ai_tags_done':
                    if err: import tkinter.messagebox as mb; mb.showerror("AI", str(err))
                    else: self.master.show_toast(f"Tags IA terminés ({res} éléments)"); self.refresh()
                elif kind == 'ai_cats_done':
                    if err: import tkinter.messagebox as mb; mb.showerror("AI", str(err))
                    else: self.master.show_toast(f"Catégories IA terminées ({res} éléments)"); self.refresh()
                elif kind == 'ai_all_done':
                    if err: import tkinter.messagebox as mb; mb.showerror("AI", str(err))
                    else: self.master.show_toast(f"IA complète terminée ({res} éléments)"); self.refresh()
        except queue.Empty: pass
        self.after(400, self._poll_ui)

    def _build_context_menu(self):
        self._tree_menu.add_command(label="Ouvrir", command=self.open_clip_editor)
        self._tree_menu.add_command(label="Supprimer", command=self.delete_clip)
        self._tree_menu.add_separator()
        self._tree_menu.add_command(label="Tags (sélection)", command=self.ai_tags_selected)
        self._tree_menu.add_command(label="Tags manquants (IA)", command=self.ai_tags_missing)
        self._tree_menu.add_separator()
        self._tree_menu.add_command(label="Catégories (sélection)", command=self.ai_cats_selected)
        self._tree_menu.add_command(label="Catégories manquantes (IA)", command=self.ai_cats_missing)
        self._tree_menu.add_separator()
        self._tree_menu.add_command(label="Tout (sélection)", command=self.ai_all_selected)
        self._tree_menu.add_separator()
        self._tree_menu.add_command(label="Export MD (sélection)", command=self.export_selected_md)
        self._tree_menu.add_command(label="Export JSON (sélection)", command=self.export_selected_json)

    def _on_tree_right_click(self, event):
        iid = self.tree.identify_row(event.y)
        if iid: self.tree.selection_set(iid)
        self._tree_menu.tk_popup(event.x_root, event.y_root)
