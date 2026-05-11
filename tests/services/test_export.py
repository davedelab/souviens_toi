import sys
from unittest.mock import MagicMock

# Mock GUI dependencies BEFORE importing any memex_next modules
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
]

for mod in mock_modules:
    sys.modules[mod] = MagicMock()

from memex_next.services.export import safe_filename

def test_safe_filename_normal():
    assert safe_filename("hello") == "hello"
    assert safe_filename("my note title") == "my note title"

def test_safe_filename_invalid_chars():
    # re.sub(r'[\\/:*?"<>|]+', '_', s)
    assert safe_filename("title/with/slashes") == "title_with_slashes"
    assert safe_filename("what?|") == "what_"
    assert safe_filename("a:b*c") == "a_b_c"

def test_safe_filename_long():
    long_title = "a" * 100
    safe = safe_filename(long_title)
    assert len(safe) == 80
    assert safe == "a" * 80

def test_safe_filename_empty():
    assert safe_filename("") == "note"

def test_safe_filename_only_invalid():
    # re.sub(r'[\\/:*?"<>|]+', '_', s) replaces the sequence of invalid chars with a single '_'
    assert safe_filename('\\/:*?"<>|') == "_"
    assert safe_filename("////") == "_"
