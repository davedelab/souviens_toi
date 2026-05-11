import sys
from unittest.mock import MagicMock

# Mock GUI and other external dependencies that might be imported transitively
for mod in [
    'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
    'tkinter.simpledialog', 'tkinter.scrolledtext', 'pyperclip', 'tkhtmlview',
    'tkcalendar', 'pypdf', 'pdfplumber', 'pytesseract', 'trafilatura',
    'markdownify', 'PIL', 'PIL.Image', 'PIL.ImageTk'
]:
    sys.modules[mod] = MagicMock()
