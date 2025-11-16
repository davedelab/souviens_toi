import tkinter as tk, tkinter.ttk as ttk, tkinter.filedialog as fd, tkinter.messagebox as mb, tkinter.simpledialog as sd
import json, pathlib, datetime as dt
from ..db import create_conn
from ..services.importer import migrate_from_db
from ..config import load_config, save_config, DB_FILE, CONFIG_FILE

class OptionsWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("Options")
        self.geometry("420x480")
        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True)

        # ---------- Interface ----------
        ui = ttk.Frame(nb)
        nb.add(ui, text='Interface')
        float_enable = tk.BooleanVar(value=self.master.floating_icons_enabled)
        ttk.Checkbutton(ui, text="Activer les icônes flottantes", variable=float_enable).pack(anchor='w', padx=12, pady=(10,6))
        tooltips_var = tk.BooleanVar(value=bool(load_config().get('tooltips_enabled', True)))
        ttk.Checkbutton(ui, text="Afficher les infobulles (tooltips)", variable=tooltips_var).pack(anchor='w', padx=12, pady=(0,6))
        captions_var = tk.BooleanVar(value=bool(load_config().get('floating_captions', False)))
        ttk.Checkbutton(ui, text="Afficher légendes sous les icônes flottantes", variable=captions_var).pack(anchor='w', padx=12, pady=(0,6))
        lang_var = tk.StringVar(value=str(load_config().get('ui_lang', 'fr')))
        lang_row = ttk.Frame(ui)
        lang_row.pack(fill='x', padx=12, pady=(6,6))
        ttk.Label(lang_row, text="Langue de l'interface").pack(side='left')
        ttk.Combobox(lang_row, values=['fr','en'], textvariable=lang_var, state='readonly', width=6).pack(side='left', padx=(8,0))
        ttk.Label(ui, text="Taille des icônes (px)").pack(anchor='w', padx=8, pady=(8,2))
        size_var = tk.IntVar(value=int(self.master.floating_icons_size))
        tk.Scale(ui, from_=36, to=80, resolution=2, orient='horizontal', variable=size_var).pack(fill='x', padx=12)
        ttk.Label(ui, text="Opacité").pack(anchor='w', padx=8, pady=(8,2))
        alpha_var = tk.DoubleVar(value=float(self.master.floating_icons_opacity))
        tk.Scale(ui, from_=0.4, to=0.9, resolution=0.05, orient='horizontal', variable=alpha_var).pack(fill='x', padx=12)
        focus_var = tk.BooleanVar(value=self.master.floating_icons_focus)
        ttk.Checkbutton(ui, text="Donner le focus à l'ouverture (icône verte)", variable=focus_var).pack(anchor='w', padx=12, pady=(8,2))
        ttk.Label(ui, text="Position par défaut (bord)").pack(anchor='w', padx=8, pady=(8,2))
        side_var = tk.StringVar(value=load_config().get('floating_icons_side', 'right'))
        side_row = ttk.Frame(ui)
        side_row.pack(anchor='w', padx=12)
        for lbl, val in (("Gauche","left"),("Droite","right"),("Haut","top"),("Bas","bottom")):
            ttk.Radiobutton(side_row, text=lbl, variable=side_var, value=val).pack(side='left', padx=4)
        def reset_pos():
            self.master.floating_icons_x = 0
            self.master.floating_icons_y = 200
            cfg = load_config()
            cfg['floating_icons_x'] = 0
            cfg['floating_icons_y'] = 200
            save_config(cfg)
            if self.master._float_win and self.master._float_win.winfo_exists():
                self.master._float_win.geometry("+0+200")
        ttk.Button(ui, text="Repositionner (0,200)", command=reset_pos).pack(anchor='w', padx=12, pady=(8,8))
        sep_var = tk.BooleanVar(value=self.master.separator_enabled)
        ttk.Checkbutton(ui, text="Ajouter séparateur --- entre blocs (buffer)", variable=sep_var).pack(anchor='w', padx=8, pady=8)

        # ---------- IA ----------
        ai = ttk.Frame(nb)
        nb.add(ai, text='IA')
        cfg = load_config()
        api_key = tk.StringVar(value=cfg.get('deepseek_api_key', ''))
        model = tk.StringVar(value=cfg.get('deepseek_model', 'deepseek-chat'))
        endpoint = tk.StringVar(value=cfg.get('deepseek_endpoint', 'https://api.deepseek.com/v1/chat/completions'))
        ai_lang = tk.StringVar(value=cfg.get('ai_lang', 'fr'))
        ai_tag_count = tk.IntVar(value=int(cfg.get('ai_tag_count', 5)))

        def row(parent, label):
            f = ttk.Frame(parent)
            f.pack(fill='x', padx=8, pady=4)
            ttk.Label(f, text=label, width=18).pack(side='left')
            return f
        r1 = row(ai, "DeepSeek API Key")
        ttk.Entry(r1, textvariable=api_key, show='*').pack(side='left', fill='x', expand=True)
        r2 = row(ai, "Modèle")
        ttk.Entry(r2, textvariable=model).pack(side='left', fill='x', expand=True)
        r3 = row(ai, "Endpoint")
        ttk.Entry(r3, textvariable=endpoint).pack(side='left', fill='x', expand=True)
        r4 = row(ai, "Langue")
        ttk.Entry(r4, textvariable=ai_lang).pack(side='left', fill='x', expand=True)
        r5 = row(ai, "Nb tags visés")
        ttk.Spinbox(r5, from_=1, to=12, textvariable=ai_tag_count, width=6).pack(side='left')

        # ---------- Tâches ----------
        tasks_tab = ttk.Frame(nb)
        nb.add(tasks_tab, text='Tâches')
        rem_enabled_var = tk.BooleanVar(value=bool(load_config().get('tasks_reminders_enabled', True)))
        ttk.Checkbutton(tasks_tab, text="Activer les rappels de tâches", variable=rem_enabled_var).pack(anchor='w', padx=8, pady=(10,6))
        row1 = ttk.Frame(tasks_tab)
        row1.pack(fill='x', padx=8, pady=4)
        ttk.Label(row1, text="Intervalle vérification (min)", width=24).pack(side='left')
        rem_interval_var = tk.IntVar(value=int(load_config().get('tasks_reminders_interval_min', 5)))
        ttk.Spinbox(row1, from_=1, to=120, textvariable=rem_interval_var, width=6).pack(side='left')
        row2 = ttk.Frame(tasks_tab)
        row2.pack(fill='x', padx=8, pady=4)
        ttk.Label(row2, text="Anticipation (min)", width=24).pack(side='left')
        rem_lead_var = tk.IntVar(value=int(load_config().get('tasks_reminders_lead_min', 30)))
        ttk.Spinbox(row2, from_=0, to=1440, textvariable=rem_lead_var, width=6).pack(side='left')

        # ---------- Catégories ----------
        cats_tab = ttk.Frame(nb)
        nb.add(cats_tab, text='Catégories')
        ttk.Label(cats_tab, text="Liste de catégories (0-2 par clip)").pack(anchor='w', padx=8, pady=(8,4))
        cats_frame = ttk.Frame(cats_tab)
        cats_frame.pack(fill='both', expand=True, padx=8, pady=4)
        self._cats_listbox = tk.Listbox(cats_frame)
        self._cats_listbox.pack(side='left', fill='both', expand=True)
        sb = ttk.Scrollbar(cats_frame, orient='vertical', command=self._cats_listbox.yview)
        self._cats_listbox.config(yscrollcommand=sb.set)
        sb.pack(side='left', fill='y')
        cfg0 = load_config()
        for cat in cfg0.get('user_categories', []):
            self._cats_listbox.insert('end', cat)
        actions = ttk.Frame(cats_tab)
        actions.pack(fill='x', padx=8, pady=4)
        def add_cat():
            name = sd.askstring("Nouvelle catégorie", "Nom de la catégorie:")
            if name: self._cats_listbox.insert('end', name.strip())
        def rename_cat():
            sel = self._cats_listbox.curselection()
            if not sel: return
            cur = self._cats_listbox.get(sel[0])
            name = sd.askstring("Renommer", "Nouveau nom:", initialvalue=cur)
            if name is not None:
                self._cats_listbox.delete(sel[0])
                self._cats_listbox.insert(sel[0], name.strip())
        def delete_cat():
            sel = self._cats_listbox.curselection()
            if not sel: return
            self._cats_listbox.delete(sel[0])
        def move_up():
            sel = self._cats_listbox.curselection()
            if not sel or sel[0] == 0: return
            i = sel[0]
            val = self._cats_listbox.get(i)
            self._cats_listbox.delete(i)
            self._cats_listbox.insert(i-1, val)
            self._cats_listbox.selection_set(i-1)
        def move_down():
            sel = self._cats_listbox.curselection()
            if not sel or sel[0] == self._cats_listbox.size()-1: return
            i = sel[0]
            val = self._cats_listbox.get(i)
            self._cats_listbox.delete(i)
            self._cats_listbox.insert(i+1, val)
            self._cats_listbox.selection_set(i+1)
        ttk.Button(actions, text="Ajouter", command=add_cat).pack(side='left', padx=2)
        ttk.Button(actions, text="Renommer", command=rename_cat).pack(side='left', padx=2)
        ttk.Button(actions, text="Supprimer", command=delete_cat).pack(side='left', padx=2)
        ttk.Button(actions, text="Monter", command=move_up).pack(side='left', padx=2)
        ttk.Button(actions, text="Descendre", command=move_down).pack(side='left', padx=2)

        # ---------- Données ----------
        data_tab = ttk.Frame(nb)
        nb.add(data_tab, text='Données')
        ttk.Label(data_tab, text="Importer depuis une ancienne base SQLite (ex: memex.db)").pack(anchor='w', padx=8, pady=(8,4))
        pick_frame = ttk.Frame(data_tab)
        pick_frame.pack(fill='x', padx=8)
        db_path_var = tk.StringVar()
        ttk.Entry(pick_frame, textvariable=db_path_var).pack(side='left', fill='x', expand=True)
        def browse_db():
            p = fd.askopenfilename(filetypes=[["SQLite","*.db"],["Tous","*.*"]])
            if p: db_path_var.set(p)
        ttk.Button(pick_frame, text="Parcourir…", command=browse_db).pack(side='left', padx=6)

        def do_import():
            path = pathlib.Path(db_path_var.get().strip())
            if not path.is_file():
                mb.showinfo("Import", "Choisis un fichier .db à importer")
                return
            def work():
                return migrate_from_db(path)
            def done(res, err):
                if err: mb.showerror("Import", f"Échec: {err}")
                else: mb.showinfo("Import", f"Import terminé: {res} éléments ajoutés")
                try: self.master.refresh()
                except Exception: pass
            from ..services.async_worker import runner
            runner.submit(work, cb=lambda r,e: self.after(0, done, r, e))
            self.master.show_toast("Import en arrière-plan…")
        ttk.Button(data_tab, text="Importer", command=do_import).pack(anchor='e', padx=8, pady=8)

        # ---------- Boutons généraux ----------
        btns = ttk.Frame(self)
        btns.pack(fill='x', pady=8)
        ttk.Button(btns, text="Annuler", command=self.destroy).pack(side='right', padx=4)
        def apply():
            # UI
            self.master.separator_enabled = bool(sep_var.get())
            self.master.floating_icons_enabled = bool(float_enable.get())
            self.master.floating_icons_size = int(size_var.get())
            self.master.floating_icons_opacity = float(alpha_var.get())
            self.master.floating_icons_focus = bool(focus_var.get())
            side = side_var.get()
            cfg = load_config()
            cfg['deepseek_api_key'] = api_key.get().strip()
            cfg['deepseek_model'] = model.get().strip() or 'deepseek-chat'
            cfg['deepseek_endpoint'] = endpoint.get().strip() or 'https://api.deepseek.com/v1/chat/completions'
            cfg['ai_lang'] = ai_lang.get().strip() or 'fr'
            cfg['ai_tag_count'] = int(ai_tag_count.get())
            cfg['floating_icons_enabled'] = self.master.floating_icons_enabled
            cfg['floating_icons_size'] = self.master.floating_icons_size
            cfg['floating_icons_opacity'] = self.master.floating_icons_opacity
            cfg['floating_icons_focus'] = self.master.floating_icons_focus
            cfg['floating_icons_side'] = side
            cfg['floating_icons_x'] = self.master.floating_icons_x
            cfg['floating_icons_y'] = self.master.floating_icons_y
            cfg['tooltips_enabled'] = bool(tooltips_var.get())
            cfg['floating_captions'] = bool(captions_var.get())
            cfg['ui_lang'] = lang_var.get() if lang_var.get() in ('fr','en') else 'fr'
            cfg['tasks_reminders_enabled'] = bool(rem_enabled_var.get())
            cfg['tasks_reminders_interval_min'] = int(rem_interval_var.get())
            cfg['tasks_reminders_lead_min'] = int(rem_lead_var.get())
            cats_vals = [self._cats_listbox.get(i) for i in range(self._cats_listbox.size())]
            cfg['user_categories'] = [c for c in (v.strip() for v in cats_vals) if c]
            save_config(cfg)
            # appliquer rappels
            try:
                self.master.reminders_enabled = bool(rem_enabled_var.get())
                self.master._reminder_interval_ms = max(1, int(rem_interval_var.get())) * 60 * 1000
                self.master._reminder_lead_sec = max(0, int(rem_lead_var.get())) * 60
                self.master._check_task_reminders()
            except Exception: pass
            # repositionner flottants
            try:
                if self.master._float_win and self.master._float_win.winfo_exists():
                    self.master._destroy_floating_icons()
                if self.master.floating_icons_enabled:
                    self.master._create_floating_icons()
            except Exception: pass
            mb.showinfo("Langue", "La modification de langue s'appliquera après redémarrage.")
            self.destroy()
        ttk.Button(btns, text="Appliquer", command=apply).pack(side='right', padx=4)
