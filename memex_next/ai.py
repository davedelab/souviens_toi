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
    
    # Essayer d'abord le parsing JSON standard
    try:
        parsed = json.loads(out)
        if "tags" in parsed and isinstance(parsed["tags"], list):
            return [t.strip() for t in parsed["tags"] if isinstance(t, str) and t.strip()][:count]
    except Exception:
        pass
    
    # Fallback: chercher un JSON dans la réponse
    try:
        import re
        json_match = re.search(r'\{[^}]*"tags"[^}]*\}', out)
        if json_match:
            parsed = json.loads(json_match.group())
            if "tags" in parsed and isinstance(parsed["tags"], list):
                return [t.strip() for t in parsed["tags"] if isinstance(t, str) and t.strip()][:count]
    except Exception:
        pass
    
    # Fallback final: extraire les mots-clés manuellement si possible
    try:
        import re
        # Chercher des patterns comme ["tag1", "tag2"] ou "tags": ["tag1", "tag2"]
        tags_match = re.search(r'"tags":\s*\[(.*?)\]', out)
        if tags_match:
            tags_str = tags_match.group(1)
            # Extraire les tags entre guillemets
            tags = re.findall(r'"([^"]+)"', tags_str)
            return [t.strip() for t in tags if t.strip()][:count]
    except Exception:
        pass
    
    return []

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

def ai_smart_summary(text: str, lang: str = "fr") -> str:
    """Résume un texte en préservant les sections marquées entre %...%"""
    cfg = load_config()
    key = cfg.get("deepseek_api_key")
    if not key:
        raise RuntimeError("Clé API manquante (Options > IA)")
    
    # Extraire les sections à préserver (entre %...%)
    import re
    preserved_sections = []
    preserved_markers = []
    
    # Trouver toutes les sections %...%
    pattern = r'%([^%]+)%'
    matches = list(re.finditer(pattern, text))
    
    for i, match in enumerate(matches):
        marker = f"__PRESERVE_{i}__"
        preserved_sections.append(match.group(1))
        preserved_markers.append(marker)
    
    # Remplacer les sections par des marqueurs temporaires
    text_to_summarize = text
    for i, match in enumerate(reversed(matches)):  # Inverser pour préserver les indices
        marker = f"__PRESERVE_{len(matches)-1-i}__"
        text_to_summarize = text_to_summarize[:match.start()] + marker + text_to_summarize[match.end():]
    
    # Créer le prompt pour l'IA
    sys_content = f"Tu es un assistant qui résume des textes en {lang}. Tu dois:"
    sys_content += "\n1. Résumer le contenu principal de manière concise et claire"
    sys_content += "\n2. Préserver EXACTEMENT les sections marquées par __PRESERVE_X__ (les remettre telles quelles)"
    sys_content += "\n3. Intégrer harmonieusement les sections préservées dans le résumé"
    
    sys = {"role": "system", "content": sys_content}
    user = {"role": "user", "content": f"Texte à résumer:\n\n{text_to_summarize}"}
    
    summary = _ai_call([sys, user], MODEL, key, cfg.get("deepseek_endpoint", ENDPOINT))
    
    # Restaurer les sections préservées
    for i, preserved_text in enumerate(preserved_sections):
        marker = f"__PRESERVE_{i}__"
        summary = summary.replace(marker, preserved_text)
    
    return summary.strip()

def ai_suggest_new_categories(text: str, existing_list: list[str], lang: str = "fr", max_n: int = 3) -> list[str]:
    """Suggère de nouvelles catégories basées sur le texte, différentes de celles existantes"""
    cfg = load_config()
    key = cfg.get("deepseek_api_key")
    if not key:
        return []
    
    existing_str = ", ".join(existing_list) if existing_list else "aucune"
    sys_content = f"Tu suggères {max_n} nouvelles catégories en {lang} pour classer ce texte. "
    sys_content += f"Évite ces catégories existantes: [{existing_str}]. "
    sys_content += "Réponds JSON: {\"categories\":[]}"
    
    sys = {"role": "system", "content": sys_content}
    user = {"role": "user", "content": f"Texte:\n{text}\n\nJSON:"}
    
    try:
        out = _ai_call([sys, user], MODEL, key, cfg.get("deepseek_endpoint", ENDPOINT))
        parsed = json.loads(out)
        if "categories" in parsed and isinstance(parsed["categories"], list):
            # Filtrer les catégories qui existent déjà
            suggestions = []
            for cat in parsed["categories"]:
                if isinstance(cat, str) and cat.strip():
                    cat_clean = cat.strip()
                    if cat_clean.lower() not in [existing.lower() for existing in existing_list]:
                        suggestions.append(cat_clean)
            return suggestions[:max_n]
    except Exception:
        pass
    
    return []
