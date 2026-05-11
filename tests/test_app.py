import sys
from unittest.mock import MagicMock

# Mock GUI and other external dependencies
mock_modules = [
    'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
    'tkinter.simpledialog', 'tkinter.scrolledtext', 'pyperclip',
    'tkhtmlview', 'tkcalendar', 'pypdf', 'pdfplumber', 'pytesseract',
    'trafilatura', 'markdownify', 'PIL', 'PIL.Image', 'PIL.ImageTk'
]
for mod in mock_modules:
    sys.modules[mod] = MagicMock()

def test_imports():
    from memex_next.ui.app import BufferApp
    assert BufferApp is not None
    from memex_next.ui.search import SearchWindow
    assert SearchWindow is not None
    from memex_next.ui.editor import EditClipWindow
    assert EditClipWindow is not None

def test_config():
    from memex_next.config import load_config
    cfg = load_config()
    assert isinstance(cfg, dict)
