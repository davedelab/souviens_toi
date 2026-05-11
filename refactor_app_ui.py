import re

def refactor_app_ui(filepath):
    with open(filepath, 'r') as f: content = f.read()

    # 1. Add _make_ui_button if not already there
    make_btn_code = """    def _make_ui_button(self, parent, text, command, tip=None, **kwargs):
        \"\"\"Standardized button creation with optional tooltip and styling.\"\"\"
        side = kwargs.pop('side', 'left')
        padx = kwargs.pop('padx', 2)
        pady = kwargs.pop('pady', 0)
        use_ttk = kwargs.pop('use_ttk', False)

        if not use_ttk:
            params = {
                'bg': "#374151", 'fg': "white",
                'activebackground': "#111827", 'relief': 'raised',
                'bd': 2, 'highlightthickness': 0
            }
            if 'w' in kwargs:
                params['width'] = kwargs.pop('w')
            params.update(kwargs)
            b = tk.Button(parent, text=text, command=command, **params)
        else:
            b = ttk.Button(parent, text=text, command=command, **kwargs)

        b.pack(side=side, padx=padx, pady=pady)

        if tip and load_config().get('tooltips_enabled', True):
            Tooltip(b, tip)
        return b
"""
    if 'def _make_ui_button' not in content:
        content = content.replace('    # ---------- UI ----------', make_btn_code + '\n    # ---------- UI ----------')

    # 2. Refactor build_ui
    new_ui_methods = """    # ---------- UI ----------
    def build_ui(self):
        \"\"\"
        Construit l'interface utilisateur flottante (Tool Window).
        \"\"\"
        self._build_main_toolbar()
        self._build_title_frame()
        self._build_tags_frame()
        self._build_categories_frame()
        self._build_markdown_toolbar()
        self._build_text_area()

    def _build_main_toolbar(self):
        top = ttk.Frame(self)
        top.pack(fill='x', padx=5, pady=5)

        self.pause_btn = self._make_ui_button(top, _tr('pause_short'), self.toggle_pause, use_ttk=True, width=4)

        self._make_ui_button(top, _tr('add'), self.add_clipboard, tip=_tr('tt_add'), w=8, bg="#f59e0b")
        self._make_ui_button(top, _tr('save'), self.send_all, tip=_tr('tt_save'), w=10, bg="#16a34a")
        self._make_ui_button(top, _tr('article'), self.capture_article, tip=_tr('tt_article'), w=8, bg="#2563eb")
        self._make_ui_button(top, _tr('md'), self.capture_selection_markdown, tip=_tr('tt_md'), w=6, bg="#0ea5e9")
        self._make_ui_button(top, _tr('file'), self.attach_file, tip=_tr('tt_file'), w=8, bg="#6b7280")

        self._make_ui_button(top, _tr('search'), self.open_search, tip=_tr('tt_search'), w=10, bg="#3b82f6")
        self._make_ui_button(top, _tr('tasks'), self.open_tasks, tip=_tr('tt_tasks'), w=8, bg="#10b981")
        self._make_ui_button(top, _tr('options'), self.open_options, tip=_tr('tt_options'), w=8, bg="#6b7280")

        self.pin_btn = self._make_ui_button(top, _tr('pin_on'), self.toggle_always_on_top, tip=_tr('tt_pin'), w=10, bg="#f59e0b", side='right')

        self.state_lbl = ttk.Label(top, text=_tr('state_active'), foreground="green")
        self.state_lbl.pack(side='left', padx=10)
        self.tick_lbl = ttk.Label(top, text="*", foreground="green", font=("Segoe", 14))

    def _build_title_frame(self):
        frm_title = ttk.LabelFrame(self, text="Titre")
        frm_title.pack(fill='x', padx=5, pady=2)
        self.title_var = tk.StringVar(value="")
        ttk.Entry(frm_title, textvariable=self.title_var).pack(side='left', fill='x', expand=True, padx=2, pady=2)
        self._make_ui_button(frm_title, "Titre", self.set_title_from_selection_or_clipboard, use_ttk=True, width=5, side='right')
        self._make_ui_button(frm_title, "AI", self.ai_title_from_buffer, use_ttk=True, width=3, side='right')
        self.read_later_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm_title, text="A lire plus tard", variable=self.read_later_var).pack(side='right', padx=6)

    def _build_tags_frame(self):
        frm_tags = ttk.LabelFrame(self, text="Tags (pour l'envoi)")
        frm_tags.pack(fill='x', padx=5, pady=2)
        self.tags_var = tk.StringVar(value="")
        tags_row = ttk.Frame(frm_tags)
        tags_row.pack(fill='x', padx=2, pady=2)
        self.tags_combo = ttk.Combobox(tags_row, textvariable=self.tags_var)
        self.tags_combo.pack(side='left', fill='x', expand=True)
        self._make_ui_button(tags_row, "AI", self.ai_fill_tags_from_buffer, use_ttk=True, width=3, side='left', padx=4)

    def _build_categories_frame(self):
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
        self._make_ui_button(cats_row, "AI", self.ai_fill_categories_from_buffer, use_ttk=True, width=3, side='left', padx=6)

    def _build_markdown_toolbar(self):
        tb = ttk.Frame(self)
        tb.pack(fill='x', padx=5, pady=(2,2))
        self._make_ui_button(tb, "B", lambda: self._md_bold_buf(), tip="Gras (Ctrl+B)", w=3, bg="#2563eb")
        self._make_ui_button(tb, "I", lambda: self._md_italic_buf(), tip="Italique (Ctrl+I)", w=3, bg="#0ea5e9")
        self._make_ui_button(tb, "Link", lambda: self._md_link_buf(), tip="Lien (Ctrl+K)", w=5, bg="#22c55e")
        self._make_ui_button(tb, "`", lambda: self._md_code_inline_buf(), tip="Code inline", w=3, bg="#6b7280")
        self._make_ui_button(tb, \"\"\"```\"\"\", lambda: self._md_code_block_buf(), tip="Bloc de code", w=5, bg="#6b7280")
        self._make_ui_button(tb, "H1", lambda: self._md_h1_buf(), tip="Titre niveau 1 (Ctrl+1)", w=4, bg="#fbbf24")
        self._make_ui_button(tb, "H2", lambda: self._md_h2_buf(), tip="Titre niveau 2 (Ctrl+2)", w=4, bg="#f59e0b")
        self._make_ui_button(tb, "H3", lambda: self._md_h3_buf(), tip="Titre niveau 3 (Ctrl+3)", w=4, bg="#d97706")
        self._make_ui_button(tb, "*", lambda: self._md_bullet_buf(), tip="Liste à  puces", w=3, bg="#8b5cf6")
        self._make_ui_button(tb, ">", lambda: self._md_quote_buf(), tip="Citation", w=3, bg="#ef4444")
        self._make_ui_button(tb, "HR", lambda: self._md_hr_buf(), tip="Ligne horizontale", w=4, bg="#10b981")
        self._make_ui_button(tb, "Undo", lambda: self._undo_buf(), tip="Annuler (Ctrl+Z)", w=5, bg="#374151")
        self._make_ui_button(tb, "Redo", lambda: self._redo_buf(), tip="Rétablir (Ctrl+Y)", w=5, bg="#374151")

    def _build_text_area(self):
        self.text_area = scrolledtext.ScrolledText(self, wrap='word', undo=True, autoseparators=True, maxundo=1000)
        self.text_area.pack(fill='both', expand=True, padx=5, pady=5)
        self._bind_editor_shortcuts()
"""
    # Replace monolithic build_ui until next section
    content = re.sub(r'    # ---------- UI ----------.*?# ---------- clipboard ----------',
                     new_ui_methods + '\n    # ---------- clipboard ----------',
                     content, flags=re.DOTALL)

    with open(filepath, 'w') as f: f.write(content)

refactor_app_ui('memex_next/ui/app.py')
