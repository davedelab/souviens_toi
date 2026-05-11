import sys
from unittest.mock import MagicMock

# Mock GUI and external dependencies before they are imported
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.simpledialog'] = MagicMock()
sys.modules['tkinter.scrolledtext'] = MagicMock()
sys.modules['pyperclip'] = MagicMock()
sys.modules['tkhtmlview'] = MagicMock()
sys.modules['tkcalendar'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageTk'] = MagicMock()

from memex_next.services.export import safe_filename

def test_safe_filename():
    assert safe_filename("hello/world") == "hello_world"
    assert safe_filename("file:name*") == "file_name_"
    assert safe_filename("") == "note"
    assert safe_filename("a" * 100) == "a" * 80
