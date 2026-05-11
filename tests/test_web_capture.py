import pytest
import datetime
from unittest.mock import patch
from memex_next.web_capture import format_web_capture_for_editor

def test_format_web_capture_success():
    web_data = {
        'success': True,
        'url': 'https://example.com',
        'title': 'Example Title'
    }
    ai_summary = "This is a great summary."

    # Mocking datetime.datetime.now() used in the function
    # The function uses __import__('datetime').datetime.now().strftime(...)
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "2023-10-27 à 12:34"

        result = format_web_capture_for_editor(web_data, ai_summary)

        assert "# 🌐 Example Title" in result
        assert "**URL :** https://example.com" in result
        assert ai_summary in result
        assert "*Capturé le 2023-10-27 à 12:34*" in result

def test_format_web_capture_no_title():
    web_data = {
        'success': True,
        'url': 'https://example.com',
    }
    ai_summary = "Summary"

    result = format_web_capture_for_editor(web_data, ai_summary)
    assert "# 🌐 Page web" in result

def test_format_web_capture_error():
    web_data = {
        'success': False,
        'url': 'https://example.com',
        'error': 'Connection timeout'
    }
    ai_summary = "Doesn't matter"

    result = format_web_capture_for_editor(web_data, ai_summary)
    assert "# 🌐 Erreur de capture" in result
    assert "**URL :** https://example.com" in result
    assert "**Erreur :** Connection timeout" in result
    assert "Doesn't matter" not in result

def test_format_web_capture_unknown_error():
    web_data = {
        'success': False,
        'url': 'https://example.com',
    }
    ai_summary = ""

    result = format_web_capture_for_editor(web_data, ai_summary)
    assert "**Erreur :** Erreur inconnue" in result
