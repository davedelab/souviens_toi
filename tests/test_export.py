import sys
from unittest.mock import MagicMock

# Mock GUI and other external dependencies before importing anything from memex_next
sys.modules["tkinter"] = MagicMock()
sys.modules["tkinter.ttk"] = MagicMock()
sys.modules["tkinter.filedialog"] = MagicMock()
sys.modules["tkinter.messagebox"] = MagicMock()
sys.modules["tkinter.simpledialog"] = MagicMock()
sys.modules["tkinter.scrolledtext"] = MagicMock()
sys.modules["pyperclip"] = MagicMock()
sys.modules["tkhtmlview"] = MagicMock()
sys.modules["tkcalendar"] = MagicMock()
sys.modules["PIL"] = MagicMock()
sys.modules["PIL.Image"] = MagicMock()
sys.modules["PIL.ImageTk"] = MagicMock()
sys.modules["pypdf"] = MagicMock()
sys.modules["pdfplumber"] = MagicMock()
sys.modules["pytesseract"] = MagicMock()
sys.modules["trafilatura"] = MagicMock()
sys.modules["markdownify"] = MagicMock()

import pytest
from memex_next.services.export import clip_to_markdown, safe_filename

def test_clip_to_markdown_basic():
    clip = {
        "title": "My Title",
        "ts": 1700000000, # 2023-11-14 22:13 UTC
        "tags": "tag1, tag2",
        "categories": "cat1",
        "type": "note",
        "source": "http://example.com",
        "raw_text": "Hello World"
    }
    result = clip_to_markdown(clip)
    assert "title: \"My Title\"" in result
    assert "date: \"2023-11-14 22:13\"" in result
    assert "tags: [tag1, tag2]" in result
    assert "categories: [cat1]" in result
    assert "type: note" in result
    assert "source: \"http://example.com\"" in result
    assert result.endswith("Hello World")

def test_clip_to_markdown_missing_fields():
    clip = {}
    result = clip_to_markdown(clip)
    assert "title: \"\"" in result
    assert "date: \"1970-01-01 00:00\"" in result
    assert "tags: []" in result
    assert "categories: []" in result
    assert "type: note" in result
    assert "source: \"\"" in result

def test_clip_to_markdown_escaping():
    clip = {"title": 'Title with "quotes"'}
    result = clip_to_markdown(clip)
    assert "title: \"Title with 'quotes'\"" in result

def test_clip_to_markdown_tags_categories_parsing():
    clip = {
        "tags": "tag1; tag2, tag3 ",
        "categories": " cat1,  cat2 "
    }
    result = clip_to_markdown(clip)
    assert "tags: [tag1, tag2, tag3]" in result
    assert "categories: [cat1, cat2]" in result

def test_safe_filename():
    assert safe_filename("normal_file") == "normal_file"
    # The regex [\\/:*?"<>|]+ collapses consecutive invalid characters
    assert safe_filename(r"file/with\chars?*") == "file_with_chars_"
    assert safe_filename("a" * 100) == "a" * 80
    assert safe_filename("") == "note"
    assert safe_filename('*:?"<>|') == "_"
    assert safe_filename("a:::b") == "a_b"
