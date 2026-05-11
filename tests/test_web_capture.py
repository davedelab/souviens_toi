import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to sys.path to resolve memex_next module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock GUI and external dependencies before importing anything from memex_next
mock_modules = [
    'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
    'tkinter.simpledialog', 'tkinter.scrolledtext', 'pyperclip',
    'tkhtmlview', 'tkcalendar', 'PIL', 'PIL.Image', 'PIL.ImageTk',
    'pypdf', 'pdfplumber', 'pytesseract', 'trafilatura', 'markdownify'
]
for module in mock_modules:
    sys.modules[module] = MagicMock()

from memex_next.web_capture import format_web_capture_for_editor  # noqa: E402


def test_format_web_capture_for_editor_success():
    web_data = {
        'success': True,
        'url': 'https://example.com',
        'title': 'Example Title'
    }
    ai_summary = "This is a summary."

    result = format_web_capture_for_editor(web_data, ai_summary)

    assert '# 🌐 Example Title' in result
    assert '**URL :** https://example.com' in result
    assert 'This is a summary.' in result
    assert 'Capturé le' in result


def test_format_web_capture_for_editor_error():
    web_data = {
        'success': False,
        'url': 'https://example.com',
        'error': 'Connection timeout'
    }
    ai_summary = "Irrelevant summary"

    result = format_web_capture_for_editor(web_data, ai_summary)

    assert '# 🌐 Erreur de capture' in result
    assert '**URL :** https://example.com' in result
    assert '**Erreur :** Connection timeout' in result
    assert 'Vérifiez votre connexion internet' in result


def test_format_web_capture_for_editor_error_no_message():
    web_data = {
        'success': False,
        'url': 'https://example.com'
    }
    ai_summary = "Irrelevant summary"

    result = format_web_capture_for_editor(web_data, ai_summary)

    assert '# 🌐 Erreur de capture' in result
    assert '**Erreur :** Erreur inconnue' in result


def test_format_web_capture_for_editor_no_title():
    web_data = {
        'success': True,
        'url': 'https://example.com'
        # title missing
    }
    ai_summary = "This is a summary."

    result = format_web_capture_for_editor(web_data, ai_summary)

    assert '# 🌐 Page web' in result
