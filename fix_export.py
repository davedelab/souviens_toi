import os
path = 'memex_next/services/export.py'
with open(path, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "f'title: \"{title.replace" in line:
        new_lines.append("    safe_title = title.replace('\"', \"'\")\n")
        new_lines.append("    front   = [\n")
        new_lines.append("        \"---\",\n")
        new_lines.append("        f'title: \"{safe_title}\"',\n")
    elif "front   = [" in line or '"---",' in line:
        continue
    else:
        new_lines.append(line)

with open(path, 'w') as f:
    f.writelines(new_lines)
