import re
path = 'memex_next/ui/app.py'
with open(path, 'r') as f: content = f.read()

# Fix bare excepts
content = content.replace('except:', 'except Exception:')

# Fix first_clip_id scoping
# We need to make it an instance attribute to survive background callbacks safely in all environments
content = content.replace('first_clip_id = None', 'self._first_clip_id_for_session = None')
content = content.replace('if first_clip_id is None:', 'if self._first_clip_id_for_session is None:')
content = content.replace('first_clip_id = clip_id', 'self._first_clip_id_for_session = clip_id')
content = content.replace('if first_clip_id:', 'if self._first_clip_id_for_session:')
content = content.replace('EditClipWindow(self, first_clip_id)', 'EditClipWindow(self, self._first_clip_id_for_session)')

with open(path, 'w') as f:
    f.write(content)
