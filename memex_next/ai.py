### memex_next/ai.py
import json, urllib.request, urllib.error
from .config import load_config

ENDPOINT = "https://api.deepseek.com/v1/chat/completions"
MODEL    = "deepseek-chat"

def _ai_call(messages, model, api_key, endpoint):
    payload = {"model": model, "messages": messages, "temperature": 0.2}
    req = urllib.request.Request(endpoint, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {api_key}')
    try:
        with urllib.request.urlopen(req, data=json.dumps(payload).encode('utf-8'), timeout=60) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data.get('choices', [{}])[0].get('message', {}).get('content', '')
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', errors='ignore')}")
    except Exception as e:
        raise RuntimeError(str(e))

def ai_generate_tags(text: str, lang: str = "fr", count: int = 5) -> list[str]:
    cfg = load_config()
    key = cfg.get("deepseek_api_key")
    if not key:
        raise RuntimeError("Clé API manquante (Options > IA)")
    sys = {"role": "system", "content": f"Tu extrais {count} tags concis en {lang}. Réponds JSON: {{\"tags\":[]}}"}
    user = {"role": "user", "content": f"Texte:\\n{text}\\n\\nJSON:"}
    out = _ai_call([sys, user], MODEL, key, cfg.get("deepseek_endpoint", ENDPOINT))
    try:
        return [t.strip() for t in json.loads(out)["tags"] if isinstance(t, str) and t.strip()][:count]
    except Exception:
        raise RuntimeError("Réponse AI invalide pour les tags")

def ai_generate_title(text: str, lang: str = "fr", max_len: int = 80) -> str:
    cfg = load_config()
    key = cfg.get("deepseek_api_key")
    if not key:
        raise RuntimeError("Clé API manquante")
    sys = {"role": "system", "content": f"Tu es un assistant qui propose des titres concis en {lang}."}
    user = {"role": "user", "content": f"Génère un titre court (={max_len} car.) sans guillemets :\\n\\n{text}"}
    out = _ai_call([sys, user], MODEL, key, cfg.get("deepseek_endpoint", ENDPOINT))
    return out.strip().strip('"\'')[:max_len]

def ai_generate_categories(text: str, user_cats: list[str], lang: str = "fr", max_n: int = 2) -> list[str]:
    cfg = load_config()
    key = cfg.get("deepseek_api_key")
    if not key or not user_cats:
        return []
    sys = {"role": "system", "content": f"Tu choisis 0 à {max_n} catégorie(s) parmi la liste fournie en {lang}. Réponds JSON: {{\"categories\":[]}}"}
    cats_join = ", ".join(user_cats)
    user = {"role": "user", "content": f"Liste: [{cats_join}]\\n\\nTexte:\\n{text}\\n\\nJSON:"}
    out = _ai_call([sys, user], MODEL, key, cfg.get("deepseek_endpoint", ENDPOINT))
    try:
        chosen = [c.strip() for c in json.loads(out)["categories"] if c.strip() in user_cats]
        return chosen[:max_n]
    except Exception:
        return []
