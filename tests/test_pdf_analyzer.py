import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import os
import sys

# Ensure memex_next is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memex_next.pdf_analyzer import extract_pdf_smart_preview

class TestPdfAnalyzer(unittest.TestCase):

    @patch('memex_next.pdf_analyzer.pdfplumber')
    @patch('memex_next.pdf_analyzer.PDFPLUMBER_AVAILABLE', True)
    @patch('os.path.getsize')
    def test_extract_pdf_smart_preview_success(self, mock_getsize, mock_pdfplumber):
        # Setup mocks
        mock_getsize.return_value = 2 * 1024 * 1024  # 2 MB

        mock_pdf = MagicMock()
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        mock_pdf.metadata = {
            'Title': 'Test Title',
            'Author': 'Test Author',
            'Subject': 'Test Subject'
        }

        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"

        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content"

        mock_pdf.pages = [mock_page1, mock_page2]

        # Call the function
        result = extract_pdf_smart_preview("dummy.pdf")

        # Assertions
        self.assertEqual(result['title'], 'Test Title')
        self.assertEqual(result['author'], 'Test Author')
        self.assertEqual(result['subject'], 'Test Subject')
        self.assertIn('=== Page 1 ===\nPage 1 content', result['preview_text'])
        self.assertIn('=== Page 2 ===\nPage 2 content', result['preview_text'])
        self.assertEqual(result['total_pages'], 2)
        self.assertEqual(result['file_size_mb'], 2.0)
        self.assertNotIn('error', result)

    @patch('memex_next.pdf_analyzer.pdfplumber')
    @patch('memex_next.pdf_analyzer.PDFPLUMBER_AVAILABLE', True)
    @patch('os.path.getsize')
    def test_extract_pdf_smart_preview_empty_pages(self, mock_getsize, mock_pdfplumber):
        # Setup mocks
        mock_getsize.return_value = 1 * 1024 * 1024

        mock_pdf = MagicMock()
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf

        mock_pdf.metadata = {}

        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "   " # Empty text

        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = None # No text

        mock_pdf.pages = [mock_page1, mock_page2]

        # Call the function
        result = extract_pdf_smart_preview("test.pdf")

        # Assertions
        self.assertEqual(result['title'], 'test') # Fallback to stem
        self.assertEqual(result['preview_text'], '')
        self.assertEqual(result['total_pages'], 2)

    @patch('memex_next.pdf_analyzer.pdfplumber')
    @patch('memex_next.pdf_analyzer.PDFPLUMBER_AVAILABLE', True)
    def test_extract_pdf_smart_preview_open_error(self, mock_pdfplumber):
        # Setup mocks
        mock_pdfplumber.open.side_effect = Exception("Open failed")

        # Call the function
        result = extract_pdf_smart_preview("error.pdf")

        # Assertions
        self.assertEqual(result['error'], 'Open failed')
        self.assertEqual(result['title'], 'error')
        self.assertEqual(result['preview_text'], '')
        self.assertEqual(result['total_pages'], 0)

    @patch('memex_next.pdf_analyzer.PDFPLUMBER_AVAILABLE', False)
    def test_extract_pdf_smart_preview_not_available(self):
        # Call the function
        result = extract_pdf_smart_preview("unavailable.pdf")

        # Assertions
        self.assertEqual(result['error'], 'pdfplumber non disponible')
        self.assertEqual(result['title'], 'unavailable')
        self.assertEqual(result['preview_text'], '')
        self.assertEqual(result['total_pages'], 0)

if __name__ == '__main__':
    unittest.main()
