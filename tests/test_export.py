import sys
from unittest.mock import MagicMock

# Mock tkinter and other GUI dependencies
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.scrolledtext'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.simpledialog'] = MagicMock()
sys.modules['pyperclip'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageTk'] = MagicMock()
sys.modules['tkhtmlview'] = MagicMock()
sys.modules['tkcalendar'] = MagicMock()

from memex_next.services.export import clip_to_markdown

def test_clip_to_markdown():
    clip = {
        "title": "Test Title",
        "ts": 1672531200,
        "tags": "tag1, tag2",
        "categories": "cat1",
        "type": "note",
        "source": "http://example.com",
        "raw_text": "Hello world"
    }
    md = clip_to_markdown(clip)
    assert 'title: "Test Title"' in md
    assert "Hello world" in md
