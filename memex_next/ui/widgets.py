### memex_next/ui/widgets.py
import tkinter as tk
import tkinter.ttk as ttk

class Tooltip:
    """Infobulle simple au survol."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)
        widget.bind("<Motion>", self.move)

    def show(self, e=None):
        if self.tip: return
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.attributes('-topmost', True)
        lbl = ttk.Label(self.tip, text=self.text, relief='solid', borderwidth=1, background='#ffffe0')
        lbl.pack(ipadx=4, ipady=2)
        self.move(e)

    def move(self, e=None):
        if not self.tip: return
        x = (e.x_root if e else self.widget.winfo_rootx()) + 12
        y = (e.y_root if e else self.widget.winfo_rooty()) + 12
        self.tip.wm_geometry(f"+{x}+{y}")

    def hide(self, e=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None
