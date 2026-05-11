import sys
from unittest.mock import MagicMock

# Mocking GUI dependencies to allow headless execution
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
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'pypdf',
    'pdfplumber',
    'pytesseract',
    'trafilatura',
    'markdownify'
]

for module in mock_modules:
    sys.modules[module] = MagicMock()

from memex_next.pdf_analyzer import format_pdf_summary_for_editor

def test_format_pdf_summary_for_editor_new_with_title():
    pdf_path = "/path/to/document.pdf"
    pdf_info = {'title': 'Scientific Paper'}
    ai_summary = "This is a summary."
    context = "new"

    result = format_pdf_summary_for_editor(pdf_path, pdf_info, ai_summary, context)

    assert "# 📄 Scientific Paper" in result
    assert "This is a summary." in result
    assert "**Source :** `document.pdf`" in result

def test_format_pdf_summary_for_editor_new_without_title():
    pdf_path = "/path/to/document.pdf"
    pdf_info = {} # No title
    ai_summary = "This is a summary."
    context = "new"

    result = format_pdf_summary_for_editor(pdf_path, pdf_info, ai_summary, context)

    # Should use filename as title fallback
    assert "# 📄 document.pdf" in result
    assert "This is a summary." in result
    assert "**Source :** `document.pdf`" in result

def test_format_pdf_summary_for_editor_existing_with_title():
    pdf_path = "/path/to/document.pdf"
    pdf_info = {'title': 'Scientific Paper'}
    ai_summary = "This is a summary."
    context = "existing"

    result = format_pdf_summary_for_editor(pdf_path, pdf_info, ai_summary, context)

    assert "## 📄 Ajout : Scientific Paper" in result
    assert "This is a summary." in result
    assert "*Fichier joint : `document.pdf`*" in result

def test_format_pdf_summary_for_editor_existing_without_title():
    pdf_path = "/path/to/document.pdf"
    pdf_info = {} # No title
    ai_summary = "This is a summary."
    context = "existing"

    result = format_pdf_summary_for_editor(pdf_path, pdf_info, ai_summary, context)

    # Should use filename as title fallback
    assert "## 📄 Ajout : document.pdf" in result
    assert "This is a summary." in result
    assert "*Fichier joint : `document.pdf`*" in result
