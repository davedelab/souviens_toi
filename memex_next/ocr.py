### memex_next/ocr.py
from io import BytesIO
from typing import Optional

def extract_text_from_blob(blob: bytes, mime: str) -> str:
    """Renvoie le texte brut d’un blob image/pdf."""
    if mime == "application/pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(blob))
            parts = [pg.extract_text() or "" for pg in reader.pages]
            return "\n".join(parts).strip()
        except Exception:
            return ""
    if mime.startswith("image/"):
        try:
            from PIL import Image
            import pytesseract
            img = Image.open(BytesIO(blob))
            return pytesseract.image_to_string(img, lang="fra+eng").strip()
        except Exception:
            return ""
    if mime.startswith("text/"):
        try:
            return blob.decode("utf-8")
        except Exception:
            try:
                return blob.decode("latin-1")
            except Exception:
                return ""
    return ""
