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

    # nettoyage + corps
    if trafilatura:
        body_html = trafilatura.extract(
            html, include_comments=False, include_tables=True,
            include_links=True, favor_recall=True, output="html"
        ) or ""
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
