path = 'memex_next/ui/search.py'
with open(path, 'r') as f: content = f.read()
content = content.replace('from ..config import load_config, save_config', 'from ..config import load_config, save_config, SEPARATOR')
content = content.replace('from ..ai import ai_generate_tags, ai_generate_categories', 'from ..ai import ai_generate_tags, ai_generate_categories, ai_generate_title')
with open(path, 'w') as f: f.write(content)
