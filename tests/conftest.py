import sys
from unittest.mock import MagicMock

# Mock GUI and heavy dependencies BEFORE any memex_next imports
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
    "PIL",
    "PIL.Image",
    "PIL.ImageTk",
    "markdownify",
    "trafilatura",
    "pypdf",
    "pdfplumber",
    "pytesseract",
]

for mod in mock_modules:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()
