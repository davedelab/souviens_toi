import pytest
from unittest.mock import MagicMock, patch
from memex_next.ocr import extract_text_from_blob

def test_extract_text_pdf_success():
    """Test successful text extraction from a PDF blob."""
    mock_reader = MagicMock()
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page 1 text"
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Page 2 text"
    mock_reader.pages = [mock_page1, mock_page2]

    with patch("pypdf.PdfReader", return_value=mock_reader):
        result = extract_text_from_blob(b"dummy pdf content", "application/pdf")
        assert result == "Page 1 text\nPage 2 text"

def test_extract_text_pdf_failure():
    """Test handling of failures during PDF text extraction."""
    with patch("pypdf.PdfReader", side_effect=Exception("PDF error")):
        result = extract_text_from_blob(b"bad pdf", "application/pdf")
        assert result == ""

def test_extract_text_image_success():
    """Test successful text extraction from an image blob using OCR."""
    mock_img = MagicMock()
    with patch("PIL.Image.open", return_value=mock_img),          patch("pytesseract.image_to_string", return_value="  Ocr text  "):
        result = extract_text_from_blob(b"dummy image content", "image/png")
        assert result == "Ocr text"

def test_extract_text_image_failure():
    """Test handling of failures during image OCR."""
    # When PIL.Image.open fails, it should return ""
    with patch("PIL.Image.open", side_effect=Exception("Image error")):
        result = extract_text_from_blob(b"bad image", "image/jpeg")
        assert result == ""

def test_extract_text_ocr_failure():
    """Test handling of failures during pytesseract execution."""
    mock_img = MagicMock()
    with patch("PIL.Image.open", return_value=mock_img),          patch("pytesseract.image_to_string", side_effect=Exception("OCR error")):
        result = extract_text_from_blob(b"dummy image content", "image/png")
        assert result == ""

def test_extract_text_utf8_success():
    """Test successful text extraction from a UTF-8 encoded blob."""
    text = "Hello world! 😊"
    blob = text.encode("utf-8")
    result = extract_text_from_blob(blob, "text/plain")
    assert result == text

def test_extract_text_latin1_success():
    """Test successful text extraction from a Latin-1 encoded blob when UTF-8 fails."""
    text = "Héllò lâtïn1"
    blob = text.encode("latin-1")
    # This blob is valid latin-1 but not valid UTF-8
    result = extract_text_from_blob(blob, "text/plain")
    assert result == text

def test_extract_text_unsupported_mime():
    """Test that unsupported MIME types return an empty string."""
    result = extract_text_from_blob(b"some content", "application/octet-stream")
    assert result == ""

def test_extract_text_empty_blob():
    """Test extraction from an empty blob."""
    result = extract_text_from_blob(b"", "text/plain")
    assert result == ""

def test_extract_text_text_mime_failure():
    """Test handling of decoding failures for text blobs."""
    # Since we can't easily patch bytes.decode, we mock the bytes object itself
    # although it's passed as an argument.

    # Let's try to pass a MagicMock that behaves like bytes but raises on decode
    mock_blob = MagicMock(spec=bytes)
    mock_blob.decode.side_effect = Exception("Decode error")

    result = extract_text_from_blob(mock_blob, "text/plain")
    assert result == ""
