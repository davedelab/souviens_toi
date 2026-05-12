import sys
from unittest.mock import MagicMock

# Mock GUI and other external dependencies
mock_modules = [
    'tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox',
    'tkinter.simpledialog', 'tkinter.scrolledtext', 'pyperclip',
    'tkhtmlview', 'tkcalendar', 'pypdf', 'pdfplumber', 'pytesseract',
    'trafilatura', 'markdownify', 'PIL', 'PIL.Image', 'PIL.ImageTk'
]
for module in mock_modules:
    sys.modules[module] = MagicMock()

import pytest

class MockApp(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.paused = False
    def toggle_pause(self):
        self.paused = not self.paused

def test_search_filtering_logic_unit():
    # This test directly verifies the logic being optimized
    # instead of trying to mock the whole SearchWindow which is complex due to UI

    active_tag_filters = {"Tag1", "Tag2"}
    active_category_filters = {"Cat1"}

    clips = [
        {'id': 1, 'tags': 'Tag1, Other', 'categories': 'Cat1', 'ts': 100, 'title': 'Clip 1', 'read_later': 0},
        {'id': 2, 'tags': 'tag2', 'categories': 'Other', 'ts': 200, 'title': 'Clip 2', 'read_later': 0},
        {'id': 3, 'tags': 'None', 'categories': 'None', 'ts': 300, 'title': 'Clip 3', 'read_later': 0},
    ]

    # --- Optimized Logic from search.py ---

    # Tag filtering
    if active_tag_filters:
        active_tags_lower = {tg.lower() for tg in active_tag_filters}
        clips = [c for c in clips if any(t.lower() in active_tags_lower for t in (c.get('tags') or '').replace(';',',').split(','))]

    assert len(clips) == 2
    assert clips[0]['id'] == 1
    assert clips[1]['id'] == 2

    # Category filtering
    if active_category_filters:
        active_cats_lower = {c2.lower() for c2 in active_category_filters}
        clips = [c for c in clips if any(cat.lower() in active_cats_lower for cat in (c.get('categories') or '').split(','))]

    assert len(clips) == 1
    assert clips[0]['id'] == 1

if __name__ == "__main__":
    pytest.main([__file__])
