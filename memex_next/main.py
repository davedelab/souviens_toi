import sys, tkinter as tk
from .ui.app import BufferApp
from .db import init_db

def entry():
    """Console-script entry point."""
    init_db()
    app = BufferApp()
    app.mainloop()

if __name__ == "__main__":
    entry()
