import sys
from unittest.mock import MagicMock

def test_import_integrity():
    # Mock GUI dependencies to allow headless import
    sys.modules["tkinter"] = MagicMock()
    sys.modules["tkinter.ttk"] = MagicMock()
    sys.modules["tkinter.scrolledtext"] = MagicMock()
    sys.modules["tkinter.filedialog"] = MagicMock()
    sys.modules["tkinter.messagebox"] = MagicMock()
    sys.modules["tkinter.simpledialog"] = MagicMock()
    sys.modules["PIL"] = MagicMock()
    sys.modules["PIL.Image"] = MagicMock()
    sys.modules["PIL.ImageTk"] = MagicMock()
    sys.modules["pyperclip"] = MagicMock()
    sys.modules["tkhtmlview"] = MagicMock()
    sys.modules["tkcalendar"] = MagicMock()
    sys.modules["pypdf"] = MagicMock()
    sys.modules["pdfplumber"] = MagicMock()
    sys.modules["pytesseract"] = MagicMock()
    sys.modules["trafilatura"] = MagicMock()
    sys.modules["markdownify"] = MagicMock()

    import memex_next.ui.app
    import memex_next.ui.search
    import memex_next.ui.editor
    import memex_next.services.export
    assert True
