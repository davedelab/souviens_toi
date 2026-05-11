from unittest.mock import MagicMock, patch
from memex_next.ocr import extract_text_from_blob

def test_extract_text_pdf_success():
    mock_reader = MagicMock()
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page 1 text"
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Page 2 text"
    mock_reader.pages = [mock_page1, mock_page2]
    with patch("pypdf.PdfReader", return_value=mock_reader):
        result = extract_text_from_blob(b"pdf", "application/pdf")
        assert result == "Page 1 text\nPage 2 text"

def test_extract_text_pdf_failure():
    with patch("pypdf.PdfReader", side_effect=Exception()):
        assert extract_text_from_blob(b"bad", "application/pdf") == ""

def test_extract_text_image_success():
    mock_img = MagicMock()
    with patch("PIL.Image.open", return_value=mock_img), \
         patch("pytesseract.image_to_string", return_value="ocr"):
        assert extract_text_from_blob(b"img", "image/png") == "ocr"

def test_extract_text_image_failure():
    with patch("PIL.Image.open", side_effect=Exception()):
        assert extract_text_from_blob(b"bad", "image/jpeg") == ""

def test_extract_text_utf8_success():
    assert extract_text_from_blob("😊".encode("utf-8"), "text/plain") == "😊"

def test_extract_text_latin1_success():
    assert extract_text_from_blob(b"\xe9", "text/plain") == "é"

def test_extract_text_unsupported_mime():
    assert extract_text_from_blob(b"...", "other") == ""

def test_extract_text_text_mime_failure():
    mock_blob = MagicMock(spec=bytes)
    mock_blob.decode.side_effect = Exception()
    assert extract_text_from_blob(mock_blob, "text/plain") == ""
