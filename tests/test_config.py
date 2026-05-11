import sys
from unittest.mock import MagicMock

# Mock GUI and other heavy dependencies
mock_modules = [
    "tkinter", "tkinter.ttk", "tkinter.scrolledtext", "tkinter.filedialog",
    "tkinter.messagebox", "tkinter.simpledialog", "pyperclip", "tkhtmlview",
    "tkcalendar", "pypdf", "pdfplumber", "pytesseract", "trafilatura",
    "markdownify", "PIL", "PIL.Image", "PIL.ImageTk"
]
for mod in mock_modules:
    sys.modules[mod] = MagicMock()

import pathlib
from memex_next.config import load_config, save_config

def test_config_load_save(tmp_path, monkeypatch):
    # Mock CONFIG_FILE to use a temporary path
    temp_config = tmp_path / "test_config.json"
    monkeypatch.setattr("memex_next.config.CONFIG_FILE", temp_config)

    # Test loading non-existent config
    assert load_config() == {}

    # Test saving and loading config
    data = {"key": "value"}
    save_config(data)
    assert load_config() == data
