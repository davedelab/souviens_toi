"""
Module de capture web intelligente avec IA
"""
import urllib.request
import urllib.parse
import urllib.error
import socket
import re
import gzip
import zlib
from typing import Dict, Optional, Tuple

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False

from .config import load_config
from .ai import _ai_call, MODEL, ENDPOINT


def _prepare_url(url: str) -> Tuple[str, urllib.parse.ParseResult, Optional[str]]:
    """Normalise et valide l'URL."""
    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme:
        url = 'https://' + url
        parsed = urllib.parse.urlparse(url)

    if parsed.scheme not in ['http', 'https']:
        return url, parsed, "URL invalide : doit commencer par http:// ou https://"

    return url, parsed, None


def _download_html(url: str, timeout: int, parsed: urllib.parse.ParseResult) -> Tuple[Optional[str], Optional[str]]:
    """Télécharge le HTML brut, gère la décompression et le décodage."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    req = urllib.request.Request(url, headers=headers)

    try:
        response = urllib.request.urlopen(req, timeout=timeout)
        raw_data = response.read()

        # Gérer la décompression
        content_encoding = response.headers.get('Content-Encoding', '').lower()
        if content_encoding == 'gzip':
            raw_data = gzip.decompress(raw_data)
        elif content_encoding == 'deflate':
            raw_data = zlib.decompress(raw_data)

        # Détecter l'encodage
        charset = 'utf-8'
        content_type = response.headers.get('Content-Type', '')
        if 'charset=' in content_type:
            charset = content_type.split('charset=')[1].split(';')[0].strip()

        return raw_data.decode(charset, errors='ignore'), None

    except urllib.error.URLError as e:
        if hasattr(e, 'reason'):
            if isinstance(e.reason, socket.gaierror):
                return None, f"Erreur DNS : Impossible de résoudre '{parsed.netloc}'. Vérifiez votre connexion internet."
            else:
                return None, f"Erreur de connexion : {e.reason}"
        else:
            return None, f"Erreur URL : {e}"
    except socket.timeout:
        return None, f"Timeout : Le site ne répond pas dans les {timeout} secondes"
    except Exception as e:
        return None, f"Erreur inattendue : {str(e)}"


def _extract_title(html: str, parsed: urllib.parse.ParseResult) -> str:
    """Extrait le titre de la page."""
    if BS4_AVAILABLE:
        soup = BeautifulSoup(html, 'html.parser')
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else parsed.netloc
    else:
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        return title_match.group(1).strip() if title_match else parsed.netloc


def _extract_content(html: str) -> str:
    """Extrait le contenu textuel principal avec plusieurs stratégies de fallback."""
    content = ""

    # 1. Trafilatura
    if TRAFILATURA_AVAILABLE:
        try:
            content = trafilatura.extract(html,
                                        output_format='txt',
                                        include_comments=False,
                                        include_tables=True,
                                        include_images=False,
                                        include_links=False)
            if content:
                return content.strip()
        except Exception:
            pass

    # 2. BeautifulSoup fallback
    if BS4_AVAILABLE:
        soup = BeautifulSoup(html, 'html.parser')
        # Supprimer les éléments indésirables
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
            element.decompose()

        # Chercher le contenu principal
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=lambda x: x and 'content' in x.lower())
        if main_content:
            content = main_content.get_text(separator='\n', strip=True)
        else:
            content = soup.get_text(separator='\n', strip=True)

    if content:
        return content

    # 3. Basic regex fallback
    # Supprimer les balises script et style
    clean_html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    clean_html = re.sub(r'<style[^>]*>.*?</style>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)
    # Extraire le texte
    text = re.sub(r'<[^>]+>', '', clean_html)
    return ' '.join(text.split())[:2000]


def extract_web_content(url: str, timeout: int = 20) -> Dict[str, str]:
    """
    Extrait le contenu d'une page web de manière robuste
    """
    result = {
        'url': url,
        'title': '',
        'content': '',
        'raw_html': '',
        'error': None,
        'success': False
    }
    
    try:
        # 1. Préparation de l'URL
        normalized_url, parsed, error = _prepare_url(url)
        if error:
            result['error'] = error
            return result
        
        # 2. Téléchargement du HTML
        html, error = _download_html(normalized_url, timeout, parsed)
        if error:
            result['error'] = error
            return result
        
        result['raw_html'] = html
        
        # 3. Extraction du titre
        result['title'] = _extract_title(html, parsed)
        
        # 4. Extraction du contenu
        result['content'] = _extract_content(html)
        
        result['success'] = True
        return result
        
    except Exception as e:
        result['error'] = f"Erreur lors de l'extraction : {str(e)}"
        return result


def ai_summarize_web_content(web_data: Dict[str, str], lang: str = "fr") -> str:
    """
    Génère un résumé IA intelligent du contenu web
    """
    cfg = load_config()
    key = cfg.get("deepseek_api_key")
    if not key:
        raise RuntimeError("Clé API manquante (Options > IA)")
    
    if not web_data.get('success') or web_data.get('error'):
        return f"❌ Impossible de résumer : {web_data.get('error', 'Erreur inconnue')}"
    
    title = web_data.get('title', 'Page sans titre')
    content = web_data.get('content', '')
    url = web_data.get('url', '')
    
    if not content.strip():
        return "❌ Aucun contenu textuel trouvé sur cette page"
    
    # Limiter le contenu pour éviter les tokens excessifs
    content_preview = content[:4000] if len(content) > 4000 else content
    
    sys_content = f"""Tu es un assistant spécialisé dans l'analyse et le résumé de contenu web.
Génère un résumé structuré et concis en {lang} qui inclut :
1. Le sujet principal et l'objectif de la page
2. Les points clés et informations importantes
3. Le type de contenu (article, blog, documentation, etc.)
4. L'utilité potentielle pour la prise de notes

Format de réponse attendu :
**Type :** [Article/Blog/Documentation/News/etc.]
**Sujet :** [Description concise du sujet]

**Points clés :**
- Point important 1
- Point important 2
- Point important 3

**Résumé :** [Synthèse en 2-3 phrases]

**Utilité :** [Pourquoi cette page pourrait être intéressante à conserver]"""

    user_content = f"""URL : {url}
Titre : {title}

Contenu de la page :
{content_preview}

Génère le résumé structuré :"""

    sys = {"role": "system", "content": sys_content}
    user = {"role": "user", "content": user_content}
    
    try:
        summary = _ai_call([sys, user], MODEL, key, cfg.get("deepseek_endpoint", ENDPOINT))
        return summary.strip()
    except Exception as e:
        return f"❌ Erreur de résumé IA : {str(e)}"


def format_web_capture_for_editor(web_data: Dict[str, str], ai_summary: str) -> str:
    """
    Formate la capture web pour insertion dans l'éditeur
    """
    url = web_data.get('url', '')
    title = web_data.get('title', 'Page web')
    
    if not web_data.get('success'):
        error = web_data.get('error', 'Erreur inconnue')
        return f"""# 🌐 Erreur de capture

**URL :** {url}
**Erreur :** {error}

*Vérifiez votre connexion internet et l'URL.*"""
    
    formatted = f"""# 🌐 {title}

**URL :** {url}

{ai_summary}

---
*Capturé le {__import__('datetime').datetime.now().strftime('%Y-%m-%d à %H:%M')}*"""
    
    return formatted


def capture_web_link_complete(url: str, lang: str = "fr") -> Dict[str, str]:
    """
    Capture complète d'un lien web : extraction + résumé IA + formatage
    """
    # 1. Extraction du contenu web
    web_data = extract_web_content(url)
    
    # 2. Résumé IA si extraction réussie
    if web_data.get('success'):
        ai_summary = ai_summarize_web_content(web_data, lang)
    else:
        ai_summary = f"❌ Impossible d'analyser : {web_data.get('error')}"
    
    # 3. Formatage pour l'éditeur
    formatted_content = format_web_capture_for_editor(web_data, ai_summary)
    
    return {
        'success': web_data.get('success', False),
        'title': web_data.get('title', 'Page web'),
        'url': url,
        'formatted_content': formatted_content,
        'raw_summary': ai_summary,
        'web_data': web_data,
        'error': web_data.get('error')
    }
