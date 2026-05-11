import sys
from unittest.mock import MagicMock

# Mock GUI and external dependencies
mock_modules = [
    'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
    'tkinter.simpledialog', 'tkinter.scrolledtext', 'pyperclip', 'PIL', 'PIL.Image', 'PIL.ImageTk',
    'tkhtmlview', 'tkcalendar', 'pypdf', 'pdfplumber', 'pytesseract', 'trafilatura', 'markdownify'
]
for mod in mock_modules:
    sys.modules[mod] = MagicMock()

def test_imports():
    import memex_next.services.export
    import memex_next.ui.app
    import memex_next.ui.editor
    import memex_next.ui.search
    import memex_next.ui.options
    import memex_next.ui.tasks
    print("Core modules imported successfully")
