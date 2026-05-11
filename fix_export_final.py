path = 'memex_next/services/export.py'
with open(path, 'r') as f: content = f.read()
# Replace the line with Python 3.10 compatible version
old_line = '        f\'title: "{title.replace(\'\"\', "\'")}"\','
new_line = '        f\'title: "{title.replace(chr(34), chr(39))}"\','
content = content.replace(old_line, new_line)
with open(path, 'w') as f: f.write(content)
