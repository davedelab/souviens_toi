p = 'memex_next/services/export.py'
with open(p, 'r') as f: lines = f.readlines()
with open(p, 'w') as f:
    for line in lines:
        if "f'title: \"{title.replace" in line:
            f.write("    safe_title = title.replace('\"', \"'\")\n")
            f.write("    front   = [\n")
            f.write("        \"---\",\n")
            f.write("        f'title: \"{safe_title}\"',\n")
        elif "front   = [" in line or '"---",' in line:
            continue
        else:
            f.write(line)
