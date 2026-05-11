import sys
from unittest.mock import MagicMock

# Mock GUI dependencies before importing memex_next
mock_modules = [
    'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
    'tkinter.simpledialog', 'tkinter.scrolledtext', 'pyperclip',
    'tkhtmlview', 'tkcalendar', 'PIL', 'PIL.Image', 'PIL.ImageTk'
]
for mod_name in mock_modules:
    sys.modules[mod_name] = MagicMock()

def test_version():
    import memex_next
    assert hasattr(memex_next, '__version__')
