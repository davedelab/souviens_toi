import sys
from unittest.mock import MagicMock

# Mock GUI and other external dependencies that might be imported transitively
mock_modules = [
    "tkinter",
    "tkinter.ttk",
    "tkinter.filedialog",
    "tkinter.messagebox",
    "tkinter.simpledialog",
    "tkinter.scrolledtext",
    "pyperclip",
    "tkhtmlview",
    "tkcalendar",
    "pypdf",
    "pdfplumber",
    "pytesseract",
    "trafilatura",
    "markdownify",
    "PIL",
    "PIL.Image",
    "PIL.ImageTk",
]

for mod_name in mock_modules:
    sys.modules[mod_name] = MagicMock()
