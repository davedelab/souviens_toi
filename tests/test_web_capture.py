import sys
from unittest.mock import MagicMock

# Mock GUI and external dependencies
mock_modules = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.simpledialog',
    'tkinter.scrolledtext',
    'pyperclip',
    'tkhtmlview',
    'tkcalendar',
    'pypdf',
    'pdfplumber',
    'pytesseract',
    'trafilatura',
    'markdownify',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk'
]

for module in mock_modules:
    sys.modules[module] = MagicMock()

import unittest
from unittest.mock import patch, MagicMock
import urllib.error
import socket
import gzip
from memex_next.web_capture import extract_web_content

class TestWebCapture(unittest.TestCase):
    def test_url_normalization(self):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = b"<html><title>Test</title><body>Content</body></html>"
            mock_response.headers = {}
            mock_urlopen.return_value = mock_response

            result = extract_web_content("example.com")
            self.assertTrue(result['success'])
            self.assertEqual(result['url'], "example.com")
            args, _ = mock_urlopen.call_args
            self.assertEqual(args[0].full_url, "https://example.com")

    def test_invalid_scheme(self):
        result = extract_web_content("ftp://example.com")
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], "URL invalide : doit commencer par http:// ou https://")

    def test_dns_error(self):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.URLError(socket.gaierror(-2, 'Name or service not known'))
            result = extract_web_content("https://nonexistent.example.com")
            self.assertFalse(result['success'])
            self.assertIn("Erreur DNS", result['error'])

    def test_timeout_error(self):
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = socket.timeout("timed out")
            result = extract_web_content("https://example.com")
            self.assertFalse(result['success'])
            self.assertIn("Timeout", result['error'])

    def test_gzip_decompression(self):
        content = b"<html><title>Gzip</title><body>Decompressed content</body></html>"
        compressed = gzip.compress(content)
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = compressed
            mock_response.headers = {'Content-Encoding': 'gzip'}
            mock_urlopen.return_value = mock_response

            result = extract_web_content("https://example.com")
            self.assertTrue(result['success'])
            self.assertIn("Gzip", result['title'])

    def test_charset_detection(self):
        content = "<html><title>Edition</title></html>".encode('latin-1')
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = content
            mock_response.headers = {'Content-Type': 'text/html; charset=latin-1'}
            mock_urlopen.return_value = mock_response

            result = extract_web_content("https://example.com")
            self.assertTrue(result['success'])
            self.assertEqual(result['title'], "Edition")

    def test_regex_fallback_title(self):
        with patch('memex_next.web_capture.BS4_AVAILABLE', False):
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = b"<html><title>Regex Title</title></html>"
                mock_response.headers = {}
                mock_urlopen.return_value = mock_response

                result = extract_web_content("https://example.com")
                self.assertEqual(result['title'], "Regex Title")

    def test_regex_fallback_content(self):
        with patch('memex_next.web_capture.BS4_AVAILABLE', False), \
             patch('memex_next.web_capture.TRAFILATURA_AVAILABLE', False):
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_response = MagicMock()
                mock_response.read.return_value = b"<html><body><script>ignore</script>Real Content</body></html>"
                mock_response.headers = {}
                mock_urlopen.return_value = mock_response

                result = extract_web_content("https://example.com")
                self.assertIn("Real Content", result['content'])
                self.assertNotIn("ignore", result['content'])

if __name__ == '__main__':
    unittest.main()
