### memex_next/scrap.py
import urllib.request, pathlib
from .config import SEPARATOR
try:
    from bs4 import BeautifulSoup, Comment
except Exception:
    BeautifulSoup = Comment = None
try:
    from markdownify import markdownify as mdconv
except Exception:
    mdconv = None
try:
    import trafilatura
except Exception:
    trafilatura = None

def capture_article(url: str) -> tuple[str, str, str]:
    """Renvoie (html_raw, markdown, titre)."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", errors="ignore")

    # titre
    if BeautifulSoup:
        soup = BeautifulSoup(html, "html.parser")
        title = (soup.title and soup.title.string) or ""
    else:
        import re
        m = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
        title = m.group(1).strip() if m else ""

    # nettoyage + corps avec filtrage agressif
    if trafilatura:
        try:
            # Configuration optimisée pour réduire le bruit
            body_html = trafilatura.extract(
                html, 
                include_comments=False, 
                include_tables=True,
                include_links=True, 
                include_images=False,  # Exclure les images
                favor_precision=True,  # Privilégier la précision vs rappel
                output_format="html"
            ) or ""
        except TypeError:
            try:
                body_html = trafilatura.extract(
                    html, include_comments=False, include_tables=True,
                    include_links=True, favor_precision=True
                ) or ""
                if body_html and not body_html.strip().startswith('<'):
                    body_html = f"<div>{body_html}</div>"
            except Exception:
                body_html = html
    else:
        # Nettoyage manuel si trafilatura absent
        if BeautifulSoup:
            soup = BeautifulSoup(html, "html.parser")
            # Supprimer les éléments de navigation/bruit
            for tag in soup(["nav", "header", "footer", "aside", "script", "style", "noscript", "iframe"]):
                tag.decompose()
            # Chercher le contenu principal
            main_content = soup.find("main") or soup.find("article") or soup.find("div", class_=lambda x: x and any(word in x.lower() for word in ["content", "article", "post", "entry"]))
            body_html = str(main_content) if main_content else str(soup.body or soup)
        else:
            body_html = html

    # markdown
    if mdconv:
        md = mdconv(body_html, heading_style="ATX", bullets="-", strip=["script", "style"])
    else:
        import re
        md = re.sub(r"<[^>]+>", "", body_html)
    md = md.replace("\r\n", "\n").replace("\r", "\n")
    return html, md.strip(), title or "Sans titre"
