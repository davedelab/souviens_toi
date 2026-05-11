p = 'memex_next/services/export.py'
with open(p, 'r') as f: content = f.read()

# Completely replace the clip_to_markdown function to be sure
import re
func_pattern = r'def clip_to_markdown\(clip: Dict\[str, Any\]\) -> str:.*?return "\\n"\.join\(front\) \+ body'
new_func = """def clip_to_markdown(clip: Dict[str, Any]) -> str:
    title   = clip.get("title", "")
    date    = dt.datetime.fromtimestamp(clip.get("ts", 0), tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
    tags    = [t.strip() for t in clip.get("tags", "").replace(";", ",").split(",") if t.strip()]
    cats    = [c.strip() for c in clip.get("categories", "").split(",") if c.strip()]
    typ     = clip.get("type", "note")
    source  = clip.get("source", "")
    body    = clip.get("raw_text", "")

    safe_title = title.replace('"', "'")
    front   = [
        "---",
        f'title: "{safe_title}"',
        f'date: "{date}"',
        f'tags: [{", ".join(tags)}]',
        f'categories: [{", ".join(cats)}]',
        f'type: {typ}',
        f'source: "{source}"',
        "---",
        ""
    ]
    return "\\n".join(front) + body"""

content = re.sub(func_pattern, new_func, content, flags=re.DOTALL)
with open(p, 'w') as f: f.write(content)
