
import sys
import types
from unittest.mock import MagicMock

# Properly mock tkinter as a package with submodules
tk = types.ModuleType('tkinter')
sys.modules['tkinter'] = tk
ttk = types.ModuleType('tkinter.ttk')
sys.modules['tkinter.ttk'] = ttk
st = types.ModuleType('tkinter.scrolledtext')
sys.modules['tkinter.scrolledtext'] = st
sd = types.ModuleType('tkinter.simpledialog')
sys.modules['tkinter.simpledialog'] = sd
mb = types.ModuleType('tkinter.messagebox')
sys.modules['tkinter.messagebox'] = mb
fd = types.ModuleType('tkinter.filedialog')
sys.modules['tkinter.filedialog'] = fd

tk.Tk = MagicMock
tk.Button = MagicMock
tk.Label = MagicMock
tk.Frame = MagicMock
tk.StringVar = MagicMock
tk.BooleanVar = MagicMock
tk.Toplevel = MagicMock
tk.TclError = Exception
tk.Event = MagicMock

ttk.Frame = MagicMock
ttk.Button = MagicMock
ttk.Label = MagicMock
ttk.Entry = MagicMock
ttk.Checkbutton = MagicMock
ttk.Combobox = MagicMock
ttk.LabelFrame = MagicMock

sys.modules['pyperclip'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['tkhtmlview'] = MagicMock()
sys.modules['tkcalendar'] = MagicMock()
sys.modules['pypdf'] = MagicMock()
sys.modules['pdfplumber'] = MagicMock()
sys.modules['pytesseract'] = MagicMock()
sys.modules['trafilatura'] = MagicMock()
sys.modules['markdownify'] = MagicMock()

import pytest
from memex_next.ui.app import BufferApp

def test_new_methods_present():
    assert hasattr(BufferApp, '_prompt_for_web_url')
    assert hasattr(BufferApp, '_save_smart_capture_to_db')
    assert hasattr(BufferApp, '_capture_article_smart')
    assert hasattr(BufferApp, 'capture_article')

def test_capture_article_logic():
    with pytest.MonkeyPatch().context() as mp:
        # Mock dependencies
        mp.setattr("memex_next.ui.app.load_config", lambda: {"auto_analyze_web": True})

        # Create a mock instance
        app = MagicMock(spec=BufferApp)
        app.capture_article = lambda: BufferApp.capture_article(app)
        app._prompt_for_web_url.return_value = "http://test.com"

        # Test smart path
        app.capture_article()
        app._capture_article_smart.assert_called_once_with("http://test.com")

        # Test classic path
        app._capture_article_smart.reset_mock()
        mp.setattr("memex_next.ui.app.load_config", lambda: {"auto_analyze_web": False})
        app.capture_article()
        app._capture_article_classic.assert_called_once_with("http://test.com")

        # Test cancel path
        app._capture_article_classic.reset_mock()
        app._prompt_for_web_url.return_value = None
        app.capture_article()
        app._capture_article_smart.assert_not_called()
        app._capture_article_classic.assert_not_called()
