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
    "PIL",
    "PIL.Image",
    "PIL.ImageTk",
    "pypdf",
    "pdfplumber",
    "pytesseract",
    "trafilatura",
    "markdownify",
]

for module_name in mock_modules:
    sys.modules[module_name] = MagicMock()
