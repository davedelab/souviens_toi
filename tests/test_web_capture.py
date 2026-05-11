import unittest
from unittest.mock import patch
import urllib.error
import socket
from memex_next.web_capture import extract_web_content

class TestWebCaptureExceptions(unittest.TestCase):

    @patch('urllib.request.urlopen')
    def test_extract_web_content_dns_error(self, mock_urlopen):
        # Setup mock to raise URLError with socket.gaierror
        reason = socket.gaierror(-2, 'Name or service not known')
        mock_urlopen.side_effect = urllib.error.URLError(reason)

        url = "https://nonexistent-domain.com"
        result = extract_web_content(url)

        self.assertFalse(result['success'])
        self.assertIn("Erreur DNS", result['error'])
        self.assertIn("nonexistent-domain.com", result['error'])
        self.assertEqual(result['url'], url)

    @patch('urllib.request.urlopen')
    def test_extract_web_content_connection_error(self, mock_urlopen):
        # Setup mock to raise URLError with a generic reason
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        url = "https://example.com"
        result = extract_web_content(url)

        self.assertFalse(result['success'])
        self.assertIn("Erreur de connexion", result['error'])
        self.assertIn("Connection refused", result['error'])

    @patch('urllib.request.urlopen')
    def test_extract_web_content_timeout(self, mock_urlopen):
        # Setup mock to raise socket.timeout
        mock_urlopen.side_effect = socket.timeout()

        url = "https://example.com"
        result = extract_web_content(url, timeout=5)

        self.assertFalse(result['success'])
        self.assertIn("Timeout", result['error'])
        self.assertIn("5 secondes", result['error'])

    @patch('urllib.request.urlopen')
    def test_extract_web_content_unexpected_exception(self, mock_urlopen):
        # Setup mock to raise a generic Exception
        mock_urlopen.side_effect = Exception("Unexpected error")

        url = "https://example.com"
        result = extract_web_content(url)

        self.assertFalse(result['success'])
        self.assertIn("Erreur inattendue", result['error'])
        self.assertIn("Unexpected error", result['error'])

if __name__ == '__main__':
    unittest.main()
