"""
Module d'analyse intelligente de PDFs avec résumé IA
"""

import os
from pathlib import Path
from typing import Dict

try:
    import pdfplumber

    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

from .config import load_config
from .ai import _ai_call, MODEL, ENDPOINT


def extract_pdf_smart_preview(pdf_path: str, max_pages: int = 5) -> Dict[str, str]:
    """
    Extrait intelligemment les informations clés d'un PDF :
    - Métadonnées (titre, auteur)
    - Premières pages (max_pages)
    - Informations structurelles
    """
    if not PDFPLUMBER_AVAILABLE:
        return {
            "error": "pdfplumber non disponible",
            "title": Path(pdf_path).stem,
            "preview_text": "",
            "total_pages": 0,
        }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Métadonnées
            metadata = pdf.metadata or {}
            title = metadata.get("Title", "") or Path(pdf_path).stem
            author = metadata.get("Author", "")
            subject = metadata.get("Subject", "")

            # Extraction des premières pages
            text_parts = []
            total_pages = len(pdf.pages)

            for i, page in enumerate(pdf.pages[:max_pages]):
                try:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text_parts.append(f"=== Page {i + 1} ===\n{page_text.strip()}")
                except Exception:
                    continue

            preview_text = "\n\n".join(text_parts)

            return {
                "title": title.strip(),
                "author": author.strip(),
                "subject": subject.strip(),
                "preview_text": preview_text,
                "total_pages": total_pages,
                "file_size_mb": round(os.path.getsize(pdf_path) / (1024 * 1024), 2),
            }

    except Exception as e:
        return {
            "error": str(e),
            "title": Path(pdf_path).stem,
            "preview_text": "",
            "total_pages": 0,
        }


def ai_summarize_pdf_preview(pdf_info: Dict[str, str], lang: str = "fr") -> str:
    """
    Génère un résumé IA intelligent basé sur l'aperçu du PDF
    """
    cfg = load_config()
    key = cfg.get("deepseek_api_key")
    if not key:
        raise RuntimeError("Clé API manquante (Options > IA)")

    if pdf_info.get("error"):
        return f"❌ Erreur d'analyse : {pdf_info['error']}"

    # Construction du prompt intelligent
    title = pdf_info.get("title", "Document sans titre")
    author = pdf_info.get("author", "")
    subject = pdf_info.get("subject", "")
    total_pages = pdf_info.get("total_pages", 0)
    preview_text = pdf_info.get("preview_text", "")
    file_size = pdf_info.get("file_size_mb", 0)

    sys_content = f"""Tu es un assistant spécialisé dans l'analyse de documents PDF. 
Génère un résumé concis et structuré en {lang} qui inclut :
1. Le type et l'objectif du document
2. Les points clés identifiables 
3. L'utilité potentielle pour la prise de notes
4. Une évaluation de la pertinence

Format de réponse attendu :
**Type :** [Article/Rapport/Guide/Livre/etc.]
**Sujet principal :** [Description concise]

**Points clés identifiés :**
- Point 1
- Point 2
- Point 3

**Utilité :** [Pourquoi ce document pourrait être intéressant]
**Pertinence :** [Évaluation rapide : ⭐⭐⭐⭐⭐]"""

    metadata_info = f"Titre: {title}"
    if author:
        metadata_info += f" | Auteur: {author}"
    if subject:
        metadata_info += f" | Sujet: {subject}"
    metadata_info += f" | Pages: {total_pages} | Taille: {file_size}MB"

    user_content = f"""Métadonnées du document :
{metadata_info}

Contenu des premières pages :
{preview_text[:3000]}...

Génère le résumé structuré :"""

    sys = {"role": "system", "content": sys_content}
    user = {"role": "user", "content": user_content}

    try:
        summary = _ai_call(
            [sys, user], MODEL, key, cfg.get("deepseek_endpoint", ENDPOINT)
        )
        return summary.strip()
    except Exception as e:
        return f"❌ Erreur de résumé IA : {str(e)}"


def format_pdf_summary_for_editor(
    pdf_path: str, pdf_info: Dict[str, str], ai_summary: str, context: str = "new"
) -> str:
    """
    Formate le résumé PDF pour insertion dans l'éditeur
    context: "new" pour nouveau clip, "existing" pour clip existant
    """
    filename = Path(pdf_path).name
    title = pdf_info.get("title", filename)

    if context == "new":
        # Format pour nouveau clip
        formatted = f"""# 📄 {title}

{ai_summary}

---
**Source :** `{filename}`"""
    else:
        # Format pour clip existant
        formatted = f"""

---

## 📄 Ajout : {title}

{ai_summary}

*Fichier joint : `{filename}`*"""

    return formatted


def analyze_pdf_complete(
    pdf_path: str, lang: str = "fr", context: str = "new"
) -> Dict[str, str]:
    """
    Analyse complète d'un PDF : extraction + résumé IA + formatage
    """
    # 1. Extraction intelligente
    pdf_info = extract_pdf_smart_preview(pdf_path)

    # 2. Résumé IA
    if not pdf_info.get("error"):
        ai_summary = ai_summarize_pdf_preview(pdf_info, lang)
    else:
        ai_summary = f"❌ Impossible d'analyser le PDF : {pdf_info['error']}"

    # 3. Formatage pour l'éditeur
    formatted_content = format_pdf_summary_for_editor(
        pdf_path, pdf_info, ai_summary, context
    )

    return {
        "success": not bool(pdf_info.get("error")),
        "title": pdf_info.get("title", Path(pdf_path).stem),
        "formatted_content": formatted_content,
        "raw_summary": ai_summary,
        "pdf_info": pdf_info,
    }
