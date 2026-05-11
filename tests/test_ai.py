import sys
from unittest.mock import MagicMock

# Mock GUI dependencies
for mod in [
    'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
    'tkinter.simpledialog', 'tkinter.scrolledtext', 'PIL', 'pyperclip',
    'tkhtmlview', 'tkcalendar', 'pypdf', 'pdfplumber', 'pytesseract',
    'trafilatura', 'markdownify'
]:
    sys.modules[mod] = MagicMock()

import pytest
from unittest.mock import patch
from memex_next.ai import ai_generate_tags

@pytest.fixture
def mock_config():
    with patch('memex_next.ai.load_config') as m:
        m.return_value = {"deepseek_api_key": "fake_key"}
        yield m

@pytest.fixture
def mock_ai_call():
    with patch('memex_next.ai._ai_call') as m:
        yield m

def test_ai_generate_tags_no_key():
    with patch('memex_next.ai.load_config') as m:
        m.return_value = {}
        with pytest.raises(RuntimeError, match="Clé API manquante"):
            ai_generate_tags("some text")

def test_ai_generate_tags_standard_json(mock_config, mock_ai_call):
    mock_ai_call.return_value = '{"tags": ["python", "testing"]}'
    tags = ai_generate_tags("some text")
    assert tags == ["python", "testing"]

def test_ai_generate_tags_fallback_embedded_json(mock_config, mock_ai_call):
    # Triggers the first fallback: re.search(r'\{[^}]*"tags"[^}]*\}', out)
    mock_ai_call.return_value = 'Here is the JSON: {"tags": ["regex", "fallback"]} hope it helps.'
    tags = ai_generate_tags("some text")
    assert tags == ["regex", "fallback"]

def test_ai_generate_tags_fallback_regex_extraction(mock_config, mock_ai_call):
    # Triggers the final fallback: re.search(r'"tags":\s*\[(.*?)\]', out)
    mock_ai_call.return_value = 'The tags are: "tags": ["manual", "extraction"]'
    tags = ai_generate_tags("some text")
    assert tags == ["manual", "extraction"]

def test_ai_generate_tags_invalid_json(mock_config, mock_ai_call):
    mock_ai_call.return_value = 'invalid'
    tags = ai_generate_tags("some text")
    assert tags == []

def test_ai_generate_tags_empty_tags(mock_config, mock_ai_call):
    mock_ai_call.return_value = '{"tags": []}'
    tags = ai_generate_tags("some text")
    assert tags == []

def test_ai_generate_tags_not_a_list(mock_config, mock_ai_call):
    mock_ai_call.return_value = '{"tags": "not a list"}'
    tags = ai_generate_tags("some text")
    assert tags == []

def test_ai_generate_tags_respect_count(mock_config, mock_ai_call):
    mock_ai_call.return_value = '{"tags": ["t1", "t2", "t3", "t4", "t5", "t6"]}'
    tags = ai_generate_tags("some text", count=3)
    assert tags == ["t1", "t2", "t3"]

def test_ai_generate_tags_clean_tags(mock_config, mock_ai_call):
    mock_ai_call.return_value = '{"tags": ["  tag1  ", "", "tag2", 123]}'
    tags = ai_generate_tags("some text")
    assert tags == ["tag1", "tag2"]

def test_ai_generate_tags_complex_response(mock_config, mock_ai_call):
    # Ensure it picks the first match and handles formatting
    mock_ai_call.return_value = 'Result:\n```json\n{"tags": ["A", "B"]}\n```\nExtra info.'
    tags = ai_generate_tags("some text")
    assert tags == ["A", "B"]
