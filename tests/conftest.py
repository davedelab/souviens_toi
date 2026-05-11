import sys
from unittest.mock import MagicMock

# Mock GUI and other external dependencies that might not be in the headless environment
# or might trigger UI windows.
mock_modules = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.simpledialog',
    'tkinter.scrolledtext',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'pyperclip',
    'tkhtmlview',
    'tkcalendar',
    'pypdf',
    'pdfplumber',
    'pytesseract',
    'trafilatura',
    'markdownify',
]

for module_name in mock_modules:
    sys.modules[module_name] = MagicMock()
