import sys
from unittest.mock import MagicMock

# Mock GUI and other external dependencies that might fail in headless environment
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

for mod_name in mock_modules:
    sys.modules[mod_name] = MagicMock()
