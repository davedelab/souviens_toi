### memex_next/ui/tasks.py
import tkinter as tk, tkinter.ttk as ttk, tkinter.messagebox as mb, tkinter.simpledialog as sd
import datetime as dt
from typing import Optional
from ..db import create_conn
try:
    from tkcalendar import DateEntry as _DateEntry
except Exception:
    _DateEntry = None

class TasksWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.title("Tâches")
        self.geometry("640x460")
        top = ttk.Frame(self)
        top.pack(fill='x', padx=8, pady=6)
        self.new_title = tk.StringVar()
        ttk.Entry(top, textvariable=self.new_title).pack(side='left', fill='x', expand=True)
        # due
        due_wrap = ttk.Frame(top)
        due_wrap.pack(side='left', padx=(6,0))
        if _DateEntry:
            self.due_date = _DateEntry(due_wrap, date_pattern='yyyy-mm-dd', width=12)
        else:
            self.due_date = ttk.Entry(due_wrap, width=12)
            self.due_date.insert(0, dt.datetime.now().strftime('%Y-%m-%d'))
        self.due_date.pack(side='left')
        self.due_hour = tk.Spinbox(due_wrap, from_=0, to=23, width=3, format="%02.0f")
        self.due_min = tk.Spinbox(due_wrap, from_=0, to=59, width=3, format="%02.0f")
        self.due_hour.delete(0, 'end'); self.due_hour.insert(0, dt.datetime.now().strftime('%H'))
        self.due_min.delete(0, 'end'); self.due_min.insert(0, dt.datetime.now().strftime('%M'))
        self.due_hour.pack(side='left', padx=(4,0))
        self.due_min.pack(side='left', padx=(2,0))
        ttk.Button(top, text="Ajouter", command=self._add).pack(side='left', padx=6)

        btns = ttk.Frame(self)
        btns.pack(fill='x', padx=8, pady=4)
        ttk.Button(btns, text="Terminer", command=self._done).pack(side='left')
        ttk.Button(btns, text="Supprimer", command=self._delete).pack(side='left', padx=6)
        ttk.Button(btns, text="Rafraîchir", command=self._refresh).pack(side='left')
        ttk.Button(btns, text="Définir échéance", command=self._set_due_selected).pack(side='right')

        cols = ("id","title","status","priority","due")
        self.tree = ttk.Treeview(self, columns=cols, show='headings', selectmode='browse')
        for c, lbl, w in (("id","#",60),("title","Titre",260),("status","Statut",80),("priority","Priorité",80),("due","Échéance",100)):
            self.tree.heading(c, text=lbl)
            self.tree.column(c, width=w, anchor='w')
        self.tree.pack(fill='both', expand=True, padx=8, pady=6)
        try: self.tree.bind("<Double-1>", self._edit_due_inline)
        except Exception: pass
        self._refresh()

    def _refresh(self):
        for it in self.tree.get_children(): self.tree.delete(it)
        conn = create_conn()
        rows = conn.execute("SELECT id, title, status, priority, due_at FROM tasks ORDER BY COALESCE(due_at, 1e18) ASC, id DESC").fetchall()
        conn.close()
        for rid, title, status, prio, due in rows:
            due_s = ''
            if due:
                try: due_s = dt.datetime.fromtimestamp(int(due), tz=dt.timezone.utc).strftime('%Y-%m-%d %H:%M')
                except Exception: due_s = str(due)
            self.tree.insert('', 'end', iid=str(rid), values=(rid, title, status, prio, due_s))

    def _add(self):
        title = self.new_title.get().strip()
        if not title: return
        due_ts = None
        try:
            if isinstance(self.due_date, ttk.Entry):
                date_str = self.due_date.get().strip()
            else:
                date_str = self.due_date.get_date().strftime('%Y-%m-%d')
            hh = int(self.due_hour.get())
            mm = int(self.due_min.get())
            if date_str:
                due_dt = dt.datetime.strptime(f"{date_str} {hh:02d}:{mm:02d}", '%Y-%m-%d %H:%M').replace(tzinfo=dt.timezone.utc)
                due_ts = int(due_dt.timestamp())
        except Exception: due_ts = None
        conn = create_conn()
        if due_ts is not None:
            conn.execute("INSERT INTO tasks(title, status, priority, due_at, created_at) VALUES(?,?,?,?,?)",
                         (title, 'pending', 'medium', due_ts, int(dt.datetime.now(dt.timezone.utc).timestamp())))
        else:
            conn.execute("INSERT INTO tasks(title, status, priority, created_at) VALUES(?,?,?,?)",
                         (title, 'pending', 'medium', int(dt.datetime.now(dt.timezone.utc).timestamp())))
        conn.commit()
        conn.close()
        self.new_title.set('')
        self._refresh()

    def _done(self):
        sel = self.tree.selection()
        if not sel: return
        tid = int(sel[0])
        conn = create_conn()
        conn.execute("UPDATE tasks SET status='done' WHERE id=?", (tid,))
        conn.commit()
        conn.close()
        self._refresh()

    def _delete(self):
        sel = self.tree.selection()
        if not sel: return
        tid = int(sel[0])
        conn = create_conn()
        conn.execute("DELETE FROM tasks WHERE id=?", (tid,))
        conn.commit()
        conn.close()
        self._refresh()

    def _set_due_selected(self):
        sel = self.tree.selection()
        if not sel: return
        tid = int(sel[0])
        due_ts = None
        try:
            if isinstance(self.due_date, ttk.Entry):
                date_str = self.due_date.get().strip()
            else:
                date_str = self.due_date.get_date().strftime('%Y-%m-%d')
            hh = int(self.due_hour.get())
            mm = int(self.due_min.get())
            if date_str:
                due_dt = dt.datetime.strptime(f"{date_str} {hh:02d}:{mm:02d}", '%Y-%m-%d %H:%M').replace(tzinfo=dt.timezone.utc)
                due_ts = int(due_dt.timestamp())
        except Exception as e:
            mb.showerror("Échéance", f"Date/heure invalide: {e}")
            return
        conn = create_conn()
        conn.execute("UPDATE tasks SET due_at=? WHERE id=?", (due_ts, tid))
        conn.commit()
        conn.close()
        self._refresh()

    def _edit_due_inline(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell": return
        col = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)
        if col != "#5" or not row: return
        tid = int(row)
        vals = self.tree.item(row, 'values')
        cur_due_str = vals[4] if len(vals) >= 5 else ''
        dlg = tk.Toplevel(self)
        dlg.transient(self)
        dlg.title("Échéance")
        frm = ttk.Frame(dlg)
        frm.pack(padx=8, pady=8, fill='x')
        if _DateEntry:
            date_w = _DateEntry(frm, date_pattern='yyyy-mm-dd', width=12)
        else:
            date_w = ttk.Entry(frm, width=12)
        hour_w = tk.Spinbox(frm, from_=0, to=23, width=3, format="%02.0f")
        min_w = tk.Spinbox(frm, from_=0, to=59, width=3, format="%02.0f")
        try:
            if cur_due_str:
                due_dt = dt.datetime.strptime(cur_due_str, '%Y-%m-%d %H:%M')
            else:
                due_dt = dt.datetime.now()
            if hasattr(date_w, 'set_date'):
                date_w.set_date(due_dt)
            else:
                date_w.insert(0, due_dt.strftime('%Y-%m-%d'))
            hour_w.insert(0, due_dt.strftime('%H'))
            min_w.insert(0, due_dt.strftime('%M'))
        except Exception: pass
        date_w.pack(side='left')
        hour_w.pack(side='left', padx=(6,0))
        min_w.pack(side='left', padx=(2,0))
        btns = ttk.Frame(dlg)
        btns.pack(padx=8, pady=8, fill='x')
        def apply():
            try:
                if isinstance(date_w, ttk.Entry):
                    date_str = date_w.get().strip()
                else:
                    date_str = date_w.get_date().strftime('%Y-%m-%d')
                hh = int(hour_w.get())
                mm = int(min_w.get())
                due_dt2 = dt.datetime.strptime(f"{date_str} {hh:02d}:{mm:02d}", '%Y-%m-%d %H:%M').replace(tzinfo=dt.timezone.utc)
                due_ts = int(due_dt2.timestamp())
            except Exception as e:
                mb.showerror("Échéance", f"Date/heure invalide: {e}")
                return
            conn = create_conn()
            conn.execute("UPDATE tasks SET due_at=? WHERE id=?", (due_ts, tid))
            conn.commit()
            conn.close()
            dlg.destroy()
            self._refresh()
        ttk.Button(btns, text="OK", command=apply).pack(side='right')
        ttk.Button(btns, text="Annuler", command=dlg.destroy).pack(side='right', padx=(0,6))
        dlg.grab_set()
        dlg.focus_force()
