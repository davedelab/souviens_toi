import sys
from unittest.mock import MagicMock

# Mock GUI dependencies before importing anything from memex_next
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

import pytest
from memex_next.services.export import safe_filename

def test_safe_filename_normal():
    assert safe_filename("simple_filename") == "simple_filename"

def test_safe_filename_invalid_chars():
    # \/:*?"<>| are invalid. + in regex means consecutive ones are replaced by a single _
    assert safe_filename("file/with:invalid*chars?\"<>|") == "file_with_invalid_chars_"

def test_safe_filename_consecutive_invalid():
    assert safe_filename("a:::b") == "a_b"
    assert safe_filename("a/\\/b") == "a_b"

def test_safe_filename_long_string():
    long_str = "A" * 100
    result = safe_filename(long_str)
    assert len(result) == 80
    assert result == "A" * 80

def test_safe_filename_empty():
    assert safe_filename("") == "note"

def test_safe_filename_only_invalid():
    # "://" becomes "_" because of the +
    assert safe_filename("://") == "_"

def test_safe_filename_results_in_underscore():
    assert safe_filename(":") == "_"
