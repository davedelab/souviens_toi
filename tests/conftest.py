import sys
from unittest.mock import MagicMock

# Mock GUI and other external dependencies to allow headless testing
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
    "PIL",
    "PIL.Image",
    "pytesseract",
    "pdfplumber",
    "trafilatura",
    "markdownify",
]

for mod_name in mock_modules:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

# Link submodules to parents for consistency when using 'from parent import child'
for mod_name in mock_modules:
    if "." in mod_name:
        parent, child = mod_name.rsplit(".", 1)
        if parent in sys.modules:
            setattr(sys.modules[parent], child, sys.modules[mod_name])
