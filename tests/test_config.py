import sys
from unittest.mock import MagicMock, patch

# Mock GUI dependencies before importing memex_next.config
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
    "pypdf",
    "pdfplumber",
    "pytesseract",
    "trafilatura",
    "markdownify",
]

for mod in mock_modules:
    sys.modules[mod] = MagicMock()

import json
import pathlib
from memex_next.config import load_config

def test_load_config_exception_fallback():
    """Test that load_config returns an empty dict when an exception occurs during reading."""
    with patch.object(pathlib.Path, 'read_text', side_effect=Exception("Read error")):
        assert load_config() == {}

def test_load_config_invalid_json():
    """Test that load_config returns an empty dict when the config file contains invalid JSON."""
    with patch.object(pathlib.Path, 'read_text', return_value="invalid json"):
        assert load_config() == {}

def test_load_config_success():
    """Test that load_config returns the expected dictionary when the config file is valid."""
    config_data = {"key": "value", "api_key": "12345"}
    with patch.object(pathlib.Path, 'read_text', return_value=json.dumps(config_data)):
        assert load_config() == config_data
