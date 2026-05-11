### memex_next/services/clipboard.py
import sys, subprocess, pathlib
try:
    import win32clipboard
except Exception:
    win32clipboard = None
import pyperclip

def get_text():
    """Multi-plateforme : renvoie le texte du presse-papiers."""
    try:
        return pyperclip.paste().strip()
    except Exception:
        return ""

def get_selected_text():
    """Tente de récupérer la sélection courante (X11/macOS/Windows)."""
    try:
        if sys.platform.startswith("linux"):
            return subprocess.check_output(["xsel", "-o"]).decode().strip()
        elif sys.platform == "darwin":
            return subprocess.check_output(["pbpaste"]).decode().strip()
        elif sys.platform == "win32" and win32clipboard:
            win32clipboard.OpenClipboard()
            try:
                data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                return (data.decode(errors="ignore") if isinstance(data, (bytes, bytearray)) else str(data)).strip()
            finally:
                win32clipboard.CloseClipboard()
    except Exception:
        return ""
