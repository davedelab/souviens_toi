import sys
from unittest.mock import MagicMock

# Mocking all UI-related and external dependencies as per the guidelines in the environment.
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.simpledialog'] = MagicMock()
sys.modules['tkinter.scrolledtext'] = MagicMock()
sys.modules['pyperclip'] = MagicMock()
sys.modules['tkhtmlview'] = MagicMock()
sys.modules['tkcalendar'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageTk'] = MagicMock()

import json
from unittest.mock import patch
from memex_next.ai import ai_suggest_new_categories

def test_ai_suggest_new_categories_logic():
    # Mocking the configuration and AI call
    with patch('memex_next.ai.load_config') as mock_load_config,          patch('memex_next.ai._ai_call') as mock_ai_call:

        mock_load_config.return_value = {"deepseek_api_key": "fake-key"}

        # Scenario: AI returns some existing and some new categories
        mock_ai_call.return_value = json.dumps({
            "categories": ["ExistingCat", "NewCat", "  AnotherNewCat  ", "EXISTINGCAT", "AlreadyPresent"]
        })

        existing_list = ["ExistingCat", "AlreadyPresent"]
        text = "Some text"

        suggestions = ai_suggest_new_categories(text, existing_list, max_n=5)

        # Expected: "NewCat", "AnotherNewCat" (trimmed)
        # "ExistingCat" and "EXISTINGCAT" should be filtered out by case-insensitive check
        # "AlreadyPresent" should be filtered out

        assert "NewCat" in suggestions
        assert "AnotherNewCat" in suggestions
        assert "ExistingCat" not in suggestions
        assert "EXISTINGCAT" not in suggestions
        assert "AlreadyPresent" not in suggestions
        assert len(suggestions) == 2
        print("Logic test passed!")

if __name__ == "__main__":
    test_ai_suggest_new_categories_logic()
