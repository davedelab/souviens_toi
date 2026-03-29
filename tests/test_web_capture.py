import unittest
from unittest.mock import patch, MagicMock
import sys

# Fully mock dependencies BEFORE importing anything from memex_next
# This avoids issues with transitive imports of tkinter etc.
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.scrolledtext'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.simpledialog'] = MagicMock()
sys.modules['tkhtmlview'] = MagicMock()
sys.modules['tkcalendar'] = MagicMock()
sys.modules['pyperclip'] = MagicMock()

# Also mock these just in case
for mod in ['requests', 'PIL', 'PIL.Image', 'markdown', 'pypdf', 'pdfplumber', 'pytesseract', 'trafilatura', 'markdownify']:
    sys.modules[mod] = MagicMock()

# Mock the submodules that might be imported
sys.modules['memex_next.config'] = MagicMock()
sys.modules['memex_next.ai'] = MagicMock()

from memex_next.web_capture import format_web_capture_for_editor

class TestWebCapture(unittest.TestCase):
    def test_format_web_capture_for_editor_success(self):
        web_data = {
            'url': 'https://example.com',
            'title': 'Example Title',
            'success': True
        }
        ai_summary = "This is an AI summary."

        # The function uses __import__('datetime').datetime.now().strftime
        # Let's mock the built-in __import__ but only for 'datetime'

        orig_import = __builtins__['__import__']
        def mocked_import(name, *args, **kwargs):
            if name == 'datetime':
                mock_dt_module = MagicMock()
                # Mock the datetime class inside the module
                mock_dt_class = MagicMock()
                mock_dt_class.now.return_value.strftime.return_value = "2023-10-27 à 14:30"
                mock_dt_module.datetime = mock_dt_class
                return mock_dt_module
            return orig_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mocked_import):
            result = format_web_capture_for_editor(web_data, ai_summary)

        expected_title = "# 🌐 Example Title"
        expected_url = "**URL :** https://example.com"
        expected_summary = "This is an AI summary."
        expected_date = "2023-10-27 à 14:30"

        self.assertIn(expected_title, result)
        self.assertIn(expected_url, result)
        self.assertIn(expected_summary, result)
        self.assertIn(expected_date, result)

    def test_format_web_capture_for_editor_error(self):
        web_data = {
            'url': 'https://example.com',
            'success': False,
            'error': 'Connection timeout'
        }
        ai_summary = "❌ Impossible d'analyser : Connection timeout"

        result = format_web_capture_for_editor(web_data, ai_summary)

        self.assertIn("# 🌐 Erreur de capture", result)
        self.assertIn("**URL :** https://example.com", result)
        self.assertIn("**Erreur :** Connection timeout", result)

    def test_format_web_capture_for_editor_default_title(self):
        web_data = {
            'url': 'https://example.com',
            'success': True
            # title missing
        }
        ai_summary = "Summary"

        # We need to mock datetime here too
        orig_import = __builtins__['__import__']
        def mocked_import(name, *args, **kwargs):
            if name == 'datetime':
                mock_dt_module = MagicMock()
                mock_dt_class = MagicMock()
                mock_dt_class.now.return_value.strftime.return_value = "2023-10-27 à 14:30"
                mock_dt_module.datetime = mock_dt_class
                return mock_dt_module
            return orig_import(name, *args, **kwargs)

        with patch('builtins.__import__', side_effect=mocked_import):
            result = format_web_capture_for_editor(web_data, ai_summary)
        self.assertIn("# 🌐 Page web", result)

if __name__ == '__main__':
    unittest.main()
