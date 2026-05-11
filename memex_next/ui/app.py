### memex_next/ui/app.py
import tkinter as tk, tkinter.ttk as ttk, threading, time, queue, datetime as dt, sys, pathlib
import tkinter.scrolledtext as scrolledtext
import pyperclip
from ..services.clipboard import get_text
from ..services.async_worker import runner
from ..config import load_config, save_config, SEPARATOR
from ..db import create_conn
from ..ai import ai_generate_tags, ai_generate_title
from .search import SearchWindow
from .editor import EditClipWindow
from .tasks import TasksWindow
from .options import OptionsWindow
from .widgets import Tooltip

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
DB_FILE = BASE_DIR / "souviens_toi.db"

_LANG = {
    'fr': {
        'add': 'Ajouter', 'save': 'Enregistrer', 'article': 'Article', 'md': 'MD', 'file': 'Fichier',
        'search': 'Recherche', 'options': 'Options', 'tasks': 'Tâches', 'pin_on': 'Epingler', 'pin_off': 'Désépingler',
        'state_active': 'ACTIF', 'state_pause': 'PAUSE', 'pause_short': 'PAU', 'run_short': 'RUN',
        'float_show': 'Voir', 'float_hide': 'Cacher', 'float_search': 'Recherche',
        'tt_add': 'Ajouter le presse-papiers au buffer', 'tt_save': 'Enregistrer le buffer dans la base',
        'tt_file': 'Joindre un fichier (PDF, image, etc.) au nouveau clip',
        'tt_article': 'Capturer un article Web (extraction + Markdown)',
        'tt_md': 'Coller la sélection Web au format Markdown', 'tt_search': 'Ouvrir la recherche',
        'tt_pin': 'Epingler la fenêtre (toujours au-dessus)', 'tt_tasks': 'Ouvrir les tâches',
        'tt_options': 'Ouvrir les options', 'undo': 'Annuler', 'redo': 'Rétablir'
    },
    'en': {
        'add': 'Add', 'save': 'Save', 'article': 'Article', 'md': 'MD', 'file': 'File',
        'search': 'Search', 'options': 'Options', 'tasks': 'Tasks', 'pin_on': 'Pin', 'pin_off': 'Unpin',
        'state_active': 'ACTIVE', 'state_pause': 'PAUSE', 'pause_short': 'PAU', 'run_short': 'RUN',
        'float_show': 'Show', 'float_hide': 'Hide', 'float_search': 'Search',
        'tt_add': 'Add clipboard to buffer', 'tt_save': 'Save buffer to database',
        'tt_file': 'Attach a file (PDF, image, etc.) to the new clip',
        'tt_article': 'Capture a web article (extraction + Markdown)',
        'tt_md': 'Paste web selection as Markdown', 'tt_search': 'Open search',
        'tt_pin': 'Pin window (always on top)', 'tt_tasks': 'Open tasks',
        'tt_options': 'Open options', 'undo': 'Undo', 'redo': 'Redo'
    }
}

def _tr(key: str) -> str:
    lang = (load_config().get("ui_lang") or "fr").lower()
    return _LANG.get(lang, _LANG["fr"]).get(key, key)

class BufferApp(tk.Tk):
    # ---------- capture web ----------
    def capture_selection_markdown(self):
        txt = get_text()
        if not txt:
            from tkinter import messagebox
            messagebox.showinfo("Markdown", "Presse-papiers vide. Copiez d'abord une sélection depuis votre navigateur.")
            return
        looks_html = ('<' in txt and '>' in txt and ('</' in txt or '<p' in txt or '<div' in txt))
        if looks_html:
            try:
                from markdownify import markdownify as _mdf
                md = _mdf(txt, heading_style="ATX")
            except Exception:
                md = txt
        else:
            md = txt
        current = self.text_area.get("1.0", "end").strip()
        if self.separator_enabled and current and not current.endswith(SEPARATOR.strip()):
            self.text_area.insert("end", SEPARATOR)
        self.text_area.insert("end", md if md.endswith("\n") else md + "\n")
        self.show_toast("Sélection collée en Markdown")    
    def __init__(self):
        super().__init__()
        self.title("Souviens-toi")
        self.geometry("600x500")
        self.paused = True  # Démarrer en mode pause
        self.last_clip = ""
        self.last_source_url = ""
        self.autotag_on_finalize = True
        self.separator_enabled = True
        self.floating_icons_enabled = True
        self.floating_icons_size = 80
        self.floating_icons_opacity = 0.6
        self.floating_icons_focus = True
        self.floating_icons_x = 0
        self.floating_icons_y = 200
        self._float_win = None
        self._search_win = None
        self._setup_config()
        self.build_ui()
        self.start_clip_watcher()
        self.after(200, self._create_floating_icons)
        self.bind("<<ClipboardUpdate>>", self.process_clip_queue)
        if sys.platform == "win32":
            self.after(0, self._setup_global_hotkey)
        self.bind_all('<Control-Alt-t>', lambda e: self.set_title_from_selection_or_clipboard())
        self._reminder_setup()
        # Mettre à jour l'interface pour refléter l'état de pause initial
        self.after(100, self._update_pause_ui)

    # ---------- config ----------
    def _setup_config(self):
        cfg = load_config()
        self.autotag_on_finalize   = bool(cfg.get("autotag_on_finalize", True))
        self.separator_enabled     = bool(cfg.get("separator_enabled", True))
        self.floating_icons_enabled= bool(cfg.get("floating_icons_enabled", True))
        self.floating_icons_size   = int(cfg.get("floating_icons_size", 80))
        self.floating_icons_opacity= float(cfg.get("floating_icons_opacity", 0.6))
        self.floating_icons_focus  = bool(cfg.get("floating_icons_focus", True))
        self.floating_icons_x      = int(cfg.get("floating_icons_x", 0))
        self.floating_icons_y      = int(cfg.get("floating_icons_y", 200))

    # ---------- UI ----------
    def build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill='x', padx=5, pady=5)

        self.pause_btn = ttk.Button(top, text=_tr('pause_short'), width=4, command=self.toggle_pause)
        self.pause_btn.pack(side='left', padx=2)

        def tbtn(parent, text, cmd, w=6, bg="#374151"):
            b = tk.Button(parent, text=text, width=w, command=cmd, bg=bg, fg="white", activebackground="#111827", relief='raised', bd=2, highlightthickness=0)
            b.pack(side='left', padx=2)
            return b

        btn_add = tbtn(top, _tr('add'), self.add_clipboard, w=8, bg="#f59e0b")
        btn_send = tbtn(top, _tr('save'), self.send_all, w=10, bg="#16a34a")
        btn_article = tbtn(top, _tr('article'), self.capture_article, w=8, bg="#2563eb")
        btn_md = tbtn(top, _tr('md'), self.capture_selection_markdown, w=6, bg="#0ea5e9")
        btn_attach = tbtn(top, _tr('file'), self.attach_file, w=8, bg="#6b7280")

        btn_search = tbtn(top, _tr('search'), self.open_search, w=10, bg="#3b82f6")
        btn_tasks = tbtn(top, _tr('tasks'), self.open_tasks, w=8, bg="#10b981")
        btn_opt = tbtn(top, _tr('options'), self.open_options, w=8, bg="#6b7280")

        self.pin_btn = tk.Button(top, text=_tr('pin_on'), width=10, command=self.toggle_always_on_top, bg="#f59e0b", fg="white", activebackground="#111827", relief='raised', bd=2, highlightthickness=0)
        self.pin_btn.pack(side='right', padx=2)

        self.state_lbl = ttk.Label(top, text=_tr('state_active'), foreground="green")
        self.state_lbl.pack(side='left', padx=10)
        self.tick_lbl = ttk.Label(top, text="*", foreground="green", font=("Segoe", 14))

        # Tooltips
        if load_config().get('tooltips_enabled', True):
            Tooltip(btn_add, _tr('tt_add'))
            Tooltip(btn_send, _tr('tt_save'))
            Tooltip(btn_attach, _tr('tt_file'))
            Tooltip(btn_article, _tr('tt_article'))
            Tooltip(btn_md, _tr('tt_md'))
            Tooltip(btn_search, _tr('tt_search'))
            Tooltip(self.pin_btn, _tr('tt_pin'))
            Tooltip(btn_tasks, _tr('tt_tasks'))
            Tooltip(btn_opt, _tr('tt_options'))

        # Titre
        frm_title = ttk.LabelFrame(self, text="Titre")
        frm_title.pack(fill='x', padx=5, pady=2)
        self.title_var = tk.StringVar(value="")
        ttk.Entry(frm_title, textvariable=self.title_var).pack(side='left', fill='x', expand=True, padx=2, pady=2)
        ttk.Button(frm_title, text="Titre", width=5, command=self.set_title_from_selection_or_clipboard).pack(side='right', padx=2)
        ttk.Button(frm_title, text="AI", width=3, command=self.ai_title_from_buffer).pack(side='right', padx=2)
        self.read_later_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm_title, text="A lire plus tard", variable=self.read_later_var).pack(side='right', padx=6)

        # Tags
        frm_tags = ttk.LabelFrame(self, text="Tags (pour l'envoi)")
        frm_tags.pack(fill='x', padx=5, pady=2)
        self.tags_var = tk.StringVar(value="")
        tags_row = ttk.Frame(frm_tags)
        tags_row.pack(fill='x', padx=2, pady=2)
        self.tags_combo = ttk.Combobox(tags_row, textvariable=self.tags_var)
        self.tags_combo.pack(side='left', fill='x', expand=True)
        ttk.Button(tags_row, text="AI", width=3, command=self.ai_fill_tags_from_buffer).pack(side='left', padx=4)

        # Catégories
        frm_cats = ttk.LabelFrame(self, text="Catégories (0-2)")
        frm_cats.pack(fill='x', padx=5, pady=2)
        cats_row = ttk.Frame(frm_cats)
        cats_row.pack(fill='x', padx=2, pady=2)
        cfg_c = load_config()
        self._user_cats_main = cfg_c.get('user_categories', [])
        self.cat1_var_buf = tk.StringVar(value="")
        self.cat2_var_buf = tk.StringVar(value="")
        state_main = 'readonly' if self._user_cats_main else 'normal'
        self.cat1_cb_buf = ttk.Combobox(cats_row, values=self._user_cats_main, textvariable=self.cat1_var_buf, state=state_main, width=24)
        self.cat2_cb_buf = ttk.Combobox(cats_row, values=self._user_cats_main, textvariable=self.cat2_var_buf, state=state_main, width=24)
        self.cat1_cb_buf.pack(side='left', fill='x', expand=True)
        self.cat2_cb_buf.pack(side='left', fill='x', expand=True, padx=(6,0))
        ttk.Button(cats_row, text="AI", width=3, command=self.ai_fill_categories_from_buffer).pack(side='left', padx=6)

        # Toolbar Markdown
        tb = ttk.Frame(self)
        tb.pack(fill='x', padx=5, pady=(2,2))
        def btn(parent, txt, tip, cmd, w=4, bg="#374151"):
            b = tk.Button(parent, text=txt, width=w, command=cmd, bg=bg, fg="white", activebackground="#111827", relief='raised', bd=2, highlightthickness=0)
            b.pack(side='left', padx=2)
            Tooltip(b, tip)
            return b
        btn(tb, "B", "Gras (Ctrl+B)", lambda: self._md_bold_buf(), w=3, bg="#2563eb")
        btn(tb, "I", "Italique (Ctrl+I)", lambda: self._md_italic_buf(), w=3, bg="#0ea5e9")
        btn(tb, "Link", "Lien (Ctrl+K)", lambda: self._md_link_buf(), w=5, bg="#22c55e")
        btn(tb, "`", "Code inline", lambda: self._md_code_inline_buf(), w=3, bg="#6b7280")
        btn(tb, "```", "Bloc de code", lambda: self._md_code_block_buf(), w=5, bg="#6b7280")
        btn(tb, "H1", "Titre niveau 1 (Ctrl+1)", lambda: self._md_h1_buf(), w=4, bg="#fbbf24")
        btn(tb, "H2", "Titre niveau 2 (Ctrl+2)", lambda: self._md_h2_buf(), w=4, bg="#f59e0b")
        btn(tb, "H3", "Titre niveau 3 (Ctrl+3)", lambda: self._md_h3_buf(), w=4, bg="#d97706")
        btn(tb, "*", "Liste à  puces", lambda: self._md_bullet_buf(), w=3, bg="#8b5cf6")
        btn(tb, ">", "Citation", lambda: self._md_quote_buf(), w=3, bg="#ef4444")
        btn(tb, "HR", "Ligne horizontale", lambda: self._md_hr_buf(), w=4, bg="#10b981")
        btn(tb, "Undo", "Annuler (Ctrl+Z)", lambda: self._undo_buf(), w=5, bg="#374151")
        btn(tb, "Redo", "Rétablir (Ctrl+Y)", lambda: self._redo_buf(), w=5, bg="#374151")

        self.text_area = scrolledtext.ScrolledText(self, wrap='word', undo=True, autoseparators=True, maxundo=1000)
        self.text_area.pack(fill='both', expand=True, padx=5, pady=5)
        self._bind_editor_shortcuts()

    # ---------- clipboard ----------
    def start_clip_watcher(self):
        def watcher():
            last = ""
            while True:
                if not self.paused:
                    txt = get_text()
                    if txt and txt != last:
                        last = txt
                        if self._looks_like_url(txt):
                            self.last_source_url = txt
                        else:
                            self.clip_queue.append(txt)
                        self.event_generate("<<ClipboardUpdate>>", when="tail")
                time.sleep(1)
        self.clip_queue = []
        threading.Thread(target=watcher, daemon=True).start()

    def process_clip_queue(self, event):
        while self.clip_queue:
            self.add_clipboard(self.clip_queue.pop(0))

    def toggle_pause(self):
        self.paused = not self.paused
        self._update_pause_ui()

    def _update_pause_ui(self):
        """Met à jour l'interface pour refléter l'état de pause"""
        label = _tr('state_pause') if self.paused else _tr('state_active')
        color = "red" if self.paused else "green"
        self.state_lbl.config(text=label, foreground=color)
        self.pause_btn.config(text=_tr('run_short') if self.paused else _tr('pause_short'))

    def toggle_always_on_top(self):
        current = self.attributes('-topmost')
        self.attributes('-topmost', not current)
        self.pin_btn.config(text=_tr('pin_on') if not current else _tr('pin_off'))
        self.show_toast("Fenêtre Epinglée" if not current else "Fenêtre Désepinglée")

    def add_clipboard(self, txt=None):
        if txt is None:
            txt = get_text()
        if not txt:
            return
        current = self.text_area.get("1.0", "end").strip()
        if self.separator_enabled and current and not current.endswith(SEPARATOR.strip()):
            self.text_area.insert("end", SEPARATOR)
        self.text_area.insert("end", txt)
        self.show_toast("Ajoutée au buffer")

    def send_all(self):
        content = self.text_area.get("1.0", "end").strip()
        if not content:
            return
        title = self.title_var.get().strip() or "Sans titre"
        tags = self.tags_var.get().strip() or "Non traitée par l'IA"
        source = self.last_source_url or ""
        cats = ", ".join({self.cat1_var_buf.get().strip(), self.cat2_var_buf.get().strip()} - {""})
        read_later = 1 if self.read_later_var.get() else 0
        conn = create_conn()
        conn.execute(
            "INSERT INTO clips(ts, source, title, type, raw_text, summary, tags, categories, read_later) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (int(dt.datetime.now(dt.timezone.utc).timestamp()), source, title, "note", content, content[:150] + "...", tags, cats, read_later)
        )
        clip_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        if source:
            conn.execute("INSERT OR IGNORE INTO source_urls(url, clip_id, created_at) VALUES (?,?,?)",
                         (source, clip_id, int(dt.datetime.now(dt.timezone.utc).timestamp())))
        conn.commit()
        conn.close()

        self.text_area.delete("1.0", "end")
        self.title_var.set("")
        self.tags_var.set("")
        self.cat1_var_buf.set("")
        self.cat2_var_buf.set("")
        self.read_later_var.set(False)
        self.tick_lbl.pack(side='left', padx=5)
        self.tick_lbl.after(1500, self.tick_lbl.pack_forget)
        self.show_toast("Enregistré")

    # ---------- markdown buffer ----------
    def _md_wrap_buf(self, left, right, placeholder=''):
        try:
            start, end = self.text_area.index('sel.first'), self.text_area.index('sel.last')
        except tk.TclError:
            start = end = None
        if start and end:
            text = self.text_area.get(start, end)
            self.text_area.delete(start, end)
            self.text_area.insert(start, f"{left}{text}{right}")
            self.text_area.tag_add('sel', start, f"{start}+{len(left)+len(text)+len(right)}c")
        else:
            idx = self.text_area.index('insert')
            self.text_area.insert(idx, f"{left}{placeholder}{right}")

    def _md_prefix_lines_buf(self, prefix):
        try:
            start, end = self.text_area.index('sel.first'), self.text_area.index('sel.last')
        except tk.TclError:
            start = end = None
        if not start or not end:
            line = self.text_area.index('insert linestart')
            self.text_area.insert(line, prefix)
            return
        cur = self.text_area.index(start + ' linestart')
        last = self.text_area.index(end + ' lineend')
        while self.text_area.compare(cur, '<=', last):
            self.text_area.insert(cur, prefix)
            cur = self.text_area.index(cur + ' +1line')

    def _md_bold_buf(self):      self._md_wrap_buf('**', '**', 'texte')
    def _md_italic_buf(self):    self._md_wrap_buf('*', '*', 'texte')
    def _md_code_inline_buf(self): self._md_wrap_buf('`', '`', 'code')
    def _md_code_block_buf(self):
        try:
            start, end = self.text_area.index('sel.first'), self.text_area.index('sel.last')
        except tk.TclError:
            start = end = None
        if not start or not end:
            idx = self.text_area.index('insert')
            self.text_area.insert(idx, "\n```\n\n```\n")
            return
        text = self.text_area.get(start, end)
        self.text_area.delete(start, end)
        self.text_area.insert(start, f"```\n{text}\n```\n")
    def _md_h1_buf(self): self._md_prefix_lines_buf('# ')
    def _md_h2_buf(self): self._md_prefix_lines_buf('## ')
    def _md_h3_buf(self): self._md_prefix_lines_buf('### ')
    def _md_bullet_buf(self): self._md_prefix_lines_buf('- ')
    def _md_quote_buf(self): self._md_prefix_lines_buf('> ')
    def _md_hr_buf(self):
        idx = self.text_area.index('insert')
        self.text_area.insert(idx, "\n---\n")
    def _md_link_buf(self):
        try:
            start, end = self.text_area.index('sel.first'), self.text_area.index('sel.last')
        except tk.TclError:
            start = end = None
        txt = ''
        if start and end:
            txt = self.text_area.get(start, end)
        from tkinter import simpledialog
        url = simpledialog.askstring("Lien", "URL:")
        if not url: return
        label = txt or simpledialog.askstring("Lien", "Texte du lien:", initialvalue=url) or url
        if start and end:
            self.text_area.delete(start, end)
            self.text_area.insert(start, f"[{label}]({url})")
        else:
            idx = self.text_area.index('insert')
            self.text_area.insert(idx, f"[{label}]({url})")

    def _undo_buf(self):
        try: self.text_area.edit_undo()
        except tk.TclError: pass
    def _redo_buf(self):
        try: self.text_area.edit_redo()
        except tk.TclError: pass

    def _bind_editor_shortcuts(self):
        for keys, func in (
            ('<Control-b>', lambda e: (self._md_bold_buf(), 'break')),
            ('<Control-i>', lambda e: (self._md_italic_buf(), 'break')),
            ('<Control-k>', lambda e: (self._md_link_buf(), 'break')),
            ('<Control-1>', lambda e: (self._md_h1_buf(), 'break')),
            ('<Control-2>', lambda e: (self._md_h2_buf(), 'break')),
            ('<Control-3>', lambda e: (self._md_h3_buf(), 'break')),
            ('<Control-z>', lambda e: (self._undo_buf(), 'break')),
            ('<Control-y>', lambda e: (self._redo_buf(), 'break')),
        ):
            self.text_area.bind(keys, func)

    # ---------- IA ----------
    def ai_title_from_buffer(self):
        text = self.text_area.get('1.0','end').strip()
        if not text:
            from tkinter import messagebox
            messagebox.showinfo("IA", "Aucun texte dans le buffer")
            return
        cfg = load_config()
        lang = cfg.get('ai_lang', 'fr')
        max_len = int(cfg.get('ai_title_max_len', 80))

        def work():
            from ..ai import ai_generate_title
            return ai_generate_title(text, lang=lang, max_len=max_len)
        def done(res, err):
            if err:
                from tkinter import messagebox
                messagebox.showerror("IA", str(err))
                return
            self.title_var.set(res or self.title_var.get())
            self.show_toast("Titre IA Appliqué")
        runner.submit(work, cb=lambda r,e: self.after(0, done, r, e))

    def ai_fill_tags_from_buffer(self):
        content = self.text_area.get('1.0','end').strip()
        if not content:
            from tkinter import messagebox
            messagebox.showinfo("IA", "Aucun texte à analyser.")
            return
        cfg = load_config()
        lang = cfg.get('ai_lang', 'fr')
        count = int(cfg.get('ai_tag_count', 5))

        def work():
            from ..ai import ai_generate_tags
            return ai_generate_tags(content, lang=lang, count=count)
        def done(res, err):
            if err:
                from tkinter import messagebox
                messagebox.showerror("IA", str(err))
            else:
                self.tags_var.set(', '.join(res or []))
                self.show_toast("Tags IA remplis")
        runner.submit(work, cb=lambda r,e: self.after(0, done, r, e))

    def ai_fill_categories_from_buffer(self):
        text = self.text_area.get('1.0','end').strip()
        if not text:
            from tkinter import messagebox
            messagebox.showinfo("IA", "Aucun texte dans le buffer")
            return
        cfg = load_config()
        user_cats = cfg.get('user_categories', [])
        if not user_cats:
            from tkinter import messagebox
            messagebox.showinfo("IA", "Aucune catégorie définie (Options > Catégories)")
            return

        def work():
            from ..ai import ai_generate_categories, ai_suggest_new_categories
            picked = ai_generate_categories(text, user_cats=user_cats, lang=cfg.get('ai_lang','fr'), max_n=1) or []
            sugg   = ai_suggest_new_categories(text, existing_list=user_cats, lang=cfg.get('ai_lang','fr'), max_n=1) or []
            return {"from_list": picked, "suggested": sugg}
        def done(res, err):
            if err:
                from tkinter import messagebox
                messagebox.showerror("IA", str(err))
                return
            from_list = (res or {}).get('from_list') or []
            suggested = (res or {}).get('suggested') or []
            self.cat1_var_buf.set(from_list[0] if len(from_list) > 0 else self.cat1_var_buf.get())
            self.cat2_var_buf.set(suggested[0] if len(suggested) > 0 else self.cat2_var_buf.get())
            self.show_toast("Catégories IA proposées")
        runner.submit(work, cb=lambda r,e: self.after(0, done, r, e))

    # ---------- web ----------
    def capture_article(self):
        from tkinter import simpledialog
        try:
            default_url = self.last_source_url or (pyperclip.paste().strip() if self._looks_like_url(pyperclip.paste().strip()) else "")
        except Exception:
            default_url = self.last_source_url or ""
        url = simpledialog.askstring("Capture Web IA", "URL de la page à capturer et analyser:", initialvalue=default_url)
        if not url: return

        cfg = load_config()
        auto_analyze_web = cfg.get('auto_analyze_web', True)
        
        if auto_analyze_web:
            # Nouvelle capture intelligente avec IA
            self.show_toast("🌐 Capture et analyse IA en cours... Veuillez patienter")
            self.after(0, lambda: self._set_ui_busy(True))
            
            def work_smart(u=url):
                from ..web_capture import capture_web_link_complete
                cfg = load_config()
                lang = cfg.get('ai_lang', 'fr')
                return capture_web_link_complete(u, lang)
            
            def done_smart(web_result, err):
                if err:
                    self.show_toast(f"❌ Erreur de capture web: {str(err)}")
                    # Fallback vers capture classique
                    self._capture_article_classic(url)
                    return
                
                if web_result and web_result.get('success'):
                    # Créer le clip avec le résumé IA
                    formatted_content = web_result['formatted_content']
                    web_title = web_result.get('title', 'Page web')
                    
                    conn = create_conn()
                    conn.execute(
                        "INSERT INTO clips(ts, source, title, type, raw_text, summary, tags, categories) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (int(dt.datetime.now(dt.timezone.utc).timestamp()), url, web_title, "web", 
                         formatted_content, formatted_content[:150] + '...', 
                         self.tags_var.get().strip() or "web", "")
                    )
                    clip_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                    
                    # Enregistrer l'URL source
                    conn.execute("INSERT OR IGNORE INTO source_urls(url, clip_id, created_at) VALUES (?,?,?)",
                                 (url, clip_id, int(dt.datetime.now(dt.timezone.utc).timestamp())))
                    
                    # Sauvegarder le HTML brut si l'option est activée
                    save_html = cfg.get('save_html_source', False)
                    if save_html:
                        raw_html = web_result.get('web_data', {}).get('raw_html', '')
                        if raw_html:
                            import hashlib
                            data = raw_html.encode('utf-8', errors='ignore')
                            sha = hashlib.sha256(data).hexdigest()
                            fn = (web_title or 'page') + '.html'
                            conn.execute("INSERT INTO files(clip_id, filename, mime, size, sha256, data) VALUES (?,?,?,?,?,?)",
                                         (clip_id, fn, 'text/html', len(data), sha, data))
                    
                    conn.commit()
                    conn.close()
                    
                    self.show_toast("✅ Page web capturée et analysée avec IA!")
                    
                    # Génération automatique des tags et catégories en arrière-plan
                    auto_tags = cfg.get('auto_generate_tags_web', True)
                    if auto_tags:
                        self._generate_web_tags_async(clip_id, formatted_content)
                    
                    # Rafraîchir la fenêtre de recherche si elle existe
                    if hasattr(self, '_search_win') and self._search_win:
                        try:
                            self._search_win.refresh_results()
                        except:
                            pass
                    
                    # Ouvrir l'éditeur
                    self.after(100, lambda: EditClipWindow(self, clip_id))
                else:
                    # Fallback vers capture classique
                    error_msg = web_result.get('error', 'Erreur inconnue')
                    self.show_toast(f"⚠️ Capture IA échouée: {error_msg}")
                    self._capture_article_classic(url)
                
                # Réactiver l'interface
                self.after(0, lambda: self._set_ui_busy(False))
            
            from ..services.async_worker import runner
            runner.submit(work_smart, cb=lambda r,e: self.after(0, done_smart, r, e))
        else:
            # Capture classique si IA désactivée
            self._capture_article_classic(url)

    def _capture_article_classic(self, url):
        """Capture classique d'article web (fallback)"""
        def work(u=url):
            from ..scrap import capture_article
            html, md, title = capture_article(u)
            from ..db import create_conn
            conn = create_conn()
            conn.execute(
                "INSERT INTO clips(ts, source, title, type, raw_text, summary, tags, categories) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (int(dt.datetime.now(dt.timezone.utc).timestamp()), u, title or "Sans titre", "web", md, md[:150] + "...", "", "")
            )
            clip_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("INSERT OR IGNORE INTO source_urls(url, clip_id, created_at) VALUES (?,?,?)",
                         (u, clip_id, int(dt.datetime.now(dt.timezone.utc).timestamp())))
            # sauve HTML brut
            import hashlib
            data = html.encode('utf-8', errors='ignore')
            sha = hashlib.sha256(data).hexdigest()
            fn = (title or pathlib.Path(u).name or 'page') + '.html'
            mime = 'text/html'
            conn.execute("INSERT INTO files(clip_id, filename, mime, size, sha256, data) VALUES (?,?,?,?,?,?)",
                         (clip_id, fn, mime, len(data), sha, data))
            conn.commit()
            conn.close()
            return clip_id
        
        def done(clip_id, err):
            if err:
                from tkinter import messagebox
                messagebox.showerror("Article", f"Erreur de capture: {str(err)}")
            else:
                self.show_toast("Article capturé en Markdown")
                if clip_id:
                    self.after(100, lambda: EditClipWindow(self, clip_id))
        
        from ..services.async_worker import runner
        runner.submit(work, cb=lambda r,e: self.after(0, done, r, e))

    def _generate_web_tags_async(self, clip_id: int, content: str):
        """Génère automatiquement les tags et catégories pour une capture web"""
        def work():
            from ..ai import ai_generate_tags, ai_generate_categories
            cfg = load_config()
            lang = cfg.get('ai_lang', 'fr')
            
            # Générer tags et catégories en parallèle
            tags = ai_generate_tags(content, lang=lang, count=5)
            categories = ai_generate_categories(content, lang=lang, count=3)
            
            # Mettre à jour la base de données
            conn = create_conn()
            current_row = conn.execute("SELECT tags, categories FROM clips WHERE id=?", (clip_id,)).fetchone()
            if current_row:
                current_tags = current_row[0] or ''
                current_cats = current_row[1] or ''
                
                # Fusionner avec les tags/catégories existants
                existing_tags = [t.strip() for t in current_tags.replace(';', ',').split(',') if t.strip()]
                existing_cats = [c.strip() for c in current_cats.split(',') if c.strip()]
                
                merged_tags = list(dict.fromkeys(existing_tags + tags))
                merged_cats = list(dict.fromkeys(existing_cats + categories))
                
                conn.execute("UPDATE clips SET tags=?, categories=? WHERE id=?",
                           (', '.join(merged_tags), ', '.join(merged_cats), clip_id))
                conn.commit()
            conn.close()
            
            return len(tags) + len(categories)
        
        def done(count, err):
            if not err and count > 0:
                self.show_toast(f"🏷️ {count} tags/catégories IA générés automatiquement")
        
        from ..services.async_worker import runner
        runner.submit(work, cb=lambda r,e: self.after(0, done, r, e))

    # ---------- files ----------
    def attach_file(self):
        from tkinter import filedialog
        paths = filedialog.askopenfilenames(
            filetypes=[["PDF","*.pdf"],["Images","*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp"],
                       ["Documents","*.txt;*.md;*.docx"],["Tous","*.*"]]
        )
        if not paths: return
        
        cfg = load_config()
        auto_analyze_pdf = cfg.get('auto_analyze_pdf', True)
        
        import hashlib, mimetypes
        added = 0
        first_clip_id = None
        
        for p in paths:
            try:
                data = pathlib.Path(p).read_bytes()
                sha = hashlib.sha256(data).hexdigest()
                mime = mimetypes.guess_type(p)[0] or 'application/octet-stream'
                title = pathlib.Path(p).name
                is_pdf = p.lower().endswith('.pdf')
                
                # Analyse PDF intelligente si activée
                if is_pdf and auto_analyze_pdf:
                    # Afficher un message d'attente plus détaillé
                    self.show_toast("📄 Numérisation PDF IA en cours... Veuillez patienter")
                    # Désactiver temporairement les boutons pour éviter les clics multiples
                    self.after(0, lambda: self._set_ui_busy(True))
                    
                    def work_pdf(pdf_path=p):
                        from ..pdf_analyzer import analyze_pdf_complete
                        cfg = load_config()
                        lang = cfg.get('ai_lang', 'fr')
                        return analyze_pdf_complete(pdf_path, lang, context="new")
                    
                    def done_pdf(pdf_result, err):
                        if err:
                            self.show_toast(f"❌ Erreur d'analyse PDF: {str(err)}")
                            # Fallback vers import classique
                            self._attach_file_classic(p, data, sha, mime, title)
                            return
                        
                        if pdf_result and pdf_result.get('success'):
                            # Créer le clip avec le résumé IA
                            formatted_content = pdf_result['formatted_content']
                            pdf_title = pdf_result.get('title', title)
                            
                            conn = create_conn()
                            conn.execute(
                                "INSERT INTO clips(ts, source, title, type, raw_text, summary, tags) "
                                "VALUES (?,?,?,?,?,?,?)",
                                (int(dt.datetime.now(dt.timezone.utc).timestamp()), "", pdf_title, "note", 
                                 formatted_content, formatted_content[:150] + '...', 
                                 self.tags_var.get().strip() or "pdf")
                            )
                            clip_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                            if first_clip_id is None: 
                                first_clip_id = clip_id
                            
                            # Joindre le fichier PDF
                            conn.execute("INSERT OR IGNORE INTO files(clip_id, filename, mime, size, sha256, data) VALUES (?,?,?,?,?,?)",
                                         (clip_id, title, mime, len(data), sha, data))
                            conn.commit()
                            conn.close()
                            
                            self.show_toast("✅ PDF analysé et importé avec résumé IA!")
                            
                            # Rafraîchir la fenêtre de recherche si elle existe
                            if hasattr(self, '_search_win') and self._search_win:
                                try:
                                    self._search_win.refresh_results()
                                except:
                                    pass
                        
                        else:
                            # Fallback vers import classique
                            self._attach_file_classic(p, data, sha, mime, title)
                        
                        # Réactiver l'interface
                        self.after(0, lambda: self._set_ui_busy(False))
                    
                    from ..services.async_worker import runner
                    runner.submit(work_pdf, cb=lambda r,e: self.after(0, done_pdf, r, e))
                else:
                    # Import classique pour non-PDF ou si analyse désactivée
                    self._attach_file_classic(p, data, sha, mime, title)
                
                added += 1
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Import", f"Echec import {pathlib.Path(p).name}: {e}")
        if added:
            self.show_toast(f"{added} fichier(s) ajouté(s)")
            if first_clip_id:
                self.after(100, lambda: EditClipWindow(self, first_clip_id))

    def _attach_file_classic(self, file_path, data, sha, mime, title):
        """Import classique de fichier sans analyse IA"""
        conn = create_conn()
        conn.execute(
            "INSERT INTO clips(ts, source, title, type, raw_text, summary, tags) "
            "VALUES (?,?,?,?,?,?,?)",
            (int(dt.datetime.now(dt.timezone.utc).timestamp()), "", title, "note", "", "", 
             self.tags_var.get().strip() or "file")
        )
        clip_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        if not hasattr(self, '_first_clip_id') or self._first_clip_id is None:
            self._first_clip_id = clip_id
        conn.execute("INSERT OR IGNORE INTO files(clip_id, filename, mime, size, sha256, data) VALUES (?,?,?,?,?,?)",
                     (clip_id, title, mime, len(data), sha, data))
        conn.commit()
        conn.close()

        # Extraction OCR/texte async (comportement original)
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
            self.show_toast("Fichier importé et indexé" if res else "Fichier importé")
        
        from ..services.async_worker import runner
        runner.submit(work, cb=lambda r,e: self.after(0, done, r, e))

    def _set_ui_busy(self, busy: bool):
        """Active/désactive l'interface pendant les opérations longues"""
        try:
            # Trouver les boutons principaux et les désactiver/activer
            for widget in self.winfo_children():
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        if hasattr(child, 'config') and 'state' in child.keys():
                            child.config(state='disabled' if busy else 'normal')
        except Exception:
            pass  # Ignore les erreurs de configuration UI

    # ---------- floating icons ----------
    def _create_floating_icons(self):
        if not self.floating_icons_enabled: return
        if self._float_win and self._float_win.winfo_exists(): return
        win = tk.Toplevel(self)
        self._float_win = win
        win.overrideredirect(True)
        win.attributes('-topmost', True)
        win.attributes('-alpha', self.floating_icons_opacity)
        # Positionnement intelligent selon le côté configuré
        self._position_floating_icons(win)
        
        # drag - lier aux événements de la fenêtre ET du frame
        win.bind('<Button-1>', self._float_on_press)
        win.bind('<B1-Motion>', self._float_on_drag)
        win.bind('<ButtonRelease-1>', self._float_save_pos)
        
        # frame
        frm = ttk.Frame(win, relief='raised', borderwidth=1)
        frm.pack()
        
        # Taille plus grande et format carré pour faciliter les clics
        btn_size = max(60, self.floating_icons_size)  # Minimum 60px
        
        def make_btn(parent, txt, tip, cmd, bg="#111827"):
            b = tk.Button(parent, text=txt, 
                         width=int(btn_size//8),  # Largeur en caractères
                         height=2,  # Hauteur fixe pour format carré
                         command=cmd, bg=bg, fg="white", 
                         activebackground="#374151", 
                         relief='raised', bd=3, 
                         highlightthickness=0,
                         font=("Segoe UI", max(10, btn_size//8), "bold"))
            b.pack(side='top', pady=1, padx=1, fill='both')
            # Permettre le drag depuis les boutons aussi
            b.bind('<Button-1>', self._float_on_press)
            b.bind('<B1-Motion>', self._float_on_drag)
            b.bind('<ButtonRelease-1>', self._float_save_pos)
            from .widgets import Tooltip
            Tooltip(b, tip)
            return b
        
        # Lier aussi le drag au frame
        frm.bind('<Button-1>', self._float_on_press)
        frm.bind('<B1-Motion>', self._float_on_drag)
        frm.bind('<ButtonRelease-1>', self._float_save_pos)
        
        make_btn(frm, _tr('float_show'), _tr('float_show'), self._float_green_click, bg="#10b981")
        make_btn(frm, _tr('float_hide'), _tr('float_hide'), self._float_red_click, bg="#ef4444")
        make_btn(frm, '🔍', _tr('float_search'), self._float_search_click, bg="#3b82f6")

    def _position_floating_icons(self, win):
        """Positionne les icônes flottantes selon la configuration"""
        cfg = load_config()
        side = cfg.get('floating_icons_side', 'right')
        
        # Attendre que la fenêtre soit créée pour obtenir les dimensions
        win.update_idletasks()
        
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        win_w = 100  # Estimation de la largeur du dock
        win_h = 200  # Estimation de la hauteur du dock
        
        if side == 'right':
            x = screen_w - win_w - 10
            y = self.floating_icons_y or screen_h // 3
        elif side == 'left':
            x = 10
            y = self.floating_icons_y or screen_h // 3
        elif side == 'top':
            x = self.floating_icons_x or screen_w // 2 - win_w // 2
            y = 10
        elif side == 'bottom':
            x = self.floating_icons_x or screen_w // 2 - win_w // 2
            y = screen_h - win_h - 50
        else:
            # Utiliser la position sauvegardée
            x = self.floating_icons_x
            y = self.floating_icons_y
        
        win.geometry(f"+{int(x)}+{int(y)}")

    def _float_on_press(self, event):
        self._drag_start = (event.x_root, event.y_root)
        self._float_pos = (self._float_win.winfo_x(), self._float_win.winfo_y())

    def _float_on_drag(self, event):
        if not hasattr(self, '_drag_start'): return
        dx = event.x_root - self._drag_start[0]
        dy = event.y_root - self._drag_start[1]
        x = max(0, self._float_pos[0] + dx)
        y = max(0, self._float_pos[1] + dy)
        self._float_win.geometry(f"+{int(x)}+{int(y)}")

    def _float_save_pos(self, event=None):
        try:
            self.floating_icons_x = int(self._float_win.winfo_x())
            self.floating_icons_y = int(self._float_win.winfo_y())
            cfg = load_config()
            cfg['floating_icons_x'] = self.floating_icons_x
            cfg['floating_icons_y'] = self.floating_icons_y
            save_config(cfg)
        except Exception: pass

    def _float_on_enter(self, event=None):
        self.deiconify()
        self.lift()

    def _float_on_leave(self, event=None):
        # Check if mouse is still over any part of the main window
        try:
            x, y = event.x_root, event.y_root
            main_x = self.winfo_rootx()
            main_y = self.winfo_rooty()
            main_w = self.winfo_width()
            main_h = self.winfo_height()
            
            # Only hide if mouse is not over main window
            if not (main_x <= x <= main_x + main_w and main_y <= y <= main_y + main_h):
                self.withdraw()
        except Exception:
            pass

    def _float_green_click(self): self.deiconify(); self.lift(); self.focus_force()
    def _float_red_click(self): self.withdraw()
    def _float_search_click(self): self.open_search()

    # ---------- divers ----------
    def show_toast(self, text):
        try:
            if hasattr(self, '_toast') and self._toast: self._toast.destroy()
        except: pass
        self._toast = tk.Toplevel(self)
        self._toast.wm_overrideredirect(True)
        self._toast.attributes('-topmost', True)
        lbl = ttk.Label(self._toast, text=text, background='#111827', foreground='white', padding=(8,4))
        lbl.pack()
        self._toast.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() - self._toast.winfo_width() - 20
        y = self.winfo_rooty() + 40
        self._toast.geometry(f"+{x}+{y}")
        self._toast.after(1200, self._toast.destroy)

    def set_title_from_selection_or_clipboard(self):
        txt = get_text()
        if txt:
            self.title_var.set(txt)
            self.show_toast("Titre rempli")
        else:
            self.show_toast("Aucune sélection ni presse-papiers")

    def _looks_like_url(self, s: str) -> bool:
        import re
        return bool(re.match(r"^https?://[\w\-\.]+(:\d+)?(/\S*)?$", s.strip()))

    # ---------- rappels ----------
    def _reminder_setup(self):
        self._reminded_ids = set()
        cfg = load_config()
        self.reminders_enabled = bool(cfg.get('tasks_reminders_enabled', True))
        interval_hours = int(cfg.get('tasks_reminders_interval_hours', 1))
        self._reminder_default_days = int(cfg.get('tasks_reminders_default_days', 1))
        self._reminder_interval_ms = max(1, interval_hours) * 60 * 60 * 1000  # heures -> ms
        self.after(15000, self._check_task_reminders)

    def _check_task_reminders(self):
        try:
            if not getattr(self, 'reminders_enabled', True):
                raise RuntimeError("off")
            now = int(dt.datetime.now(dt.timezone.utc).timestamp())
            
            conn = create_conn()
            # Récupérer toutes les tâches en attente avec échéance
            rows = conn.execute(
                "SELECT id, title, due_at, reminder_days FROM tasks WHERE status='pending' AND due_at IS NOT NULL"
            ).fetchall()
            conn.close()
            
            for tid, title, due_at, reminder_days in rows:
                if tid in self._reminded_ids: continue
                
                # Calculer le délai de rappel pour cette tâche
                if reminder_days is not None:
                    if reminder_days == 0:
                        continue  # Pas de rappel pour cette tâche
                    lead_seconds = reminder_days * 24 * 60 * 60
                else:
                    # Utiliser la valeur par défaut
                    lead_seconds = self._reminder_default_days * 24 * 60 * 60
                
                # Vérifier si le rappel doit être déclenché
                reminder_time = due_at - lead_seconds
                if now >= reminder_time:
                    # Calculer le temps restant pour un message plus informatif
                    time_left = due_at - now
                    if time_left > 0:
                        days_left = time_left // (24 * 60 * 60)
                        hours_left = (time_left % (24 * 60 * 60)) // (60 * 60)
                        
                        if days_left > 0:
                            time_msg = f"dans {days_left} jour(s)"
                        elif hours_left > 0:
                            time_msg = f"dans {hours_left}h"
                        else:
                            time_msg = "très bientôt"
                        
                        self.show_toast(f"⏰ Rappel: {title} - Échéance {time_msg}")
                    else:
                        self.show_toast(f"🚨 Échéance dépassée: {title}")
                    
                    self._reminded_ids.add(tid)
                    
        except Exception: pass
        self.after(self._reminder_interval_ms, self._check_task_reminders)

    # ---------- fenàƒÂªtres ----------
    def open_search(self):
        if self._search_win and self._search_win.winfo_exists():
            self._search_win.destroy()
        self._search_win = SearchWindow(self)

    def open_tasks(self):
        TasksWindow(self)

    def open_options(self):
        OptionsWindow(self)

    # ---------- hotkeys ----------
    def _setup_global_hotkey(self):
        try:
            import ctypes, ctypes.wintypes as wt
        except Exception: return
        user32 = ctypes.windll.user32
        MOD_CONTROL = 0x0002
        MOD_SHIFT   = 0x0004
        VK_M = 0x4D
        WM_HOTKEY = 0x0312
        if not user32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_SHIFT, VK_M): return
        def loop():
            msg = wt.MSG()
            while True:
                if user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                    if msg.message == WM_HOTKEY and msg.wParam == 1:
                        self.event_generate("<<GlobalPasteSend>>", when="tail")
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))
                else: break
        threading.Thread(target=loop, daemon=True).start()
        self.bind("<<GlobalPasteSend>>", lambda e: self.paste_and_send())
