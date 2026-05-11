import sys
from unittest.mock import MagicMock

# Mock GUI and other external dependencies before they are imported
# This allows running tests in a headless environment
mock_modules = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.simpledialog',
    'tkinter.scrolledtext',
    'pyperclip',
    'tkhtmlview',
    'tkcalendar',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
]

for module_name in mock_modules:
    sys.modules[module_name] = MagicMock()
