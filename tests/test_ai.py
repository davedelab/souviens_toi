import pytest
from unittest.mock import patch
from memex_next.ai import ai_generate_tags

def test_ai_generate_tags_success():
    """Test standard JSON parsing success."""
    with patch("memex_next.ai.load_config") as mock_load:
        mock_load.return_value = {"deepseek_api_key": "test_key"}
        with patch("memex_next.ai._ai_call") as mock_call:
            mock_call.return_value = '{"tags": ["tag1", "tag2", "tag3"]}'
            tags = ai_generate_tags("some text", count=2)
            assert tags == ["tag1", "tag2"]
            assert len(tags) == 2

def test_ai_generate_tags_fallback_embedded_json():
    """Test fallback parsing when JSON is embedded in text."""
    with patch("memex_next.ai.load_config") as mock_load:
        mock_load.return_value = {"deepseek_api_key": "test_key"}
        with patch("memex_next.ai._ai_call") as mock_call:
            mock_call.return_value = 'Here is the result: {"tags": ["extracted", "tags"]} hope you like it.'
            tags = ai_generate_tags("some text")
            assert tags == ["extracted", "tags"]

def test_ai_generate_tags_fallback_regex():
    """Test fallback parsing using regex when json.loads fails but \"tags\": [...] is present."""
    with patch("memex_next.ai.load_config") as mock_load:
        mock_load.return_value = {"deepseek_api_key": "test_key"}
        with patch("memex_next.ai._ai_call") as mock_call:
            # Improperly escaped or malformed JSON that regex might still catch
            mock_call.return_value = '"tags": ["tagA", "tagB"]'
            tags = ai_generate_tags("some text")
            assert tags == ["tagA", "tagB"]

def test_ai_generate_tags_missing_key():
    """Test handling of missing API key."""
    with patch("memex_next.ai.load_config") as mock_load:
        mock_load.return_value = {}
        with pytest.raises(RuntimeError, match="Clé API manquante"):
            ai_generate_tags("some text")

def test_ai_generate_tags_invalid_response():
    """Test handling of invalid/empty AI responses."""
    with patch("memex_next.ai.load_config") as mock_load:
        mock_load.return_value = {"deepseek_api_key": "test_key"}
        with patch("memex_next.ai._ai_call") as mock_call:
            mock_call.return_value = "No tags here"
            tags = ai_generate_tags("some text")
            assert tags == []

def test_ai_generate_tags_non_list_tags():
    """Test handling when 'tags' is not a list in JSON."""
    with patch("memex_next.ai.load_config") as mock_load:
        mock_load.return_value = {"deepseek_api_key": "test_key"}
        with patch("memex_next.ai._ai_call") as mock_call:
            mock_call.return_value = '{"tags": "not a list"}'
            tags = ai_generate_tags("some text")
            assert tags == []

def test_ai_generate_tags_whitespace_and_empty():
    """Test that tags are stripped and empty tags are ignored."""
    with patch("memex_next.ai.load_config") as mock_load:
        mock_load.return_value = {"deepseek_api_key": "test_key"}
        with patch("memex_next.ai._ai_call") as mock_call:
            mock_call.return_value = '{"tags": ["  tag1  ", "", "  ", "tag2"]}'
            tags = ai_generate_tags("some text")
            assert tags == ["tag1", "tag2"]
