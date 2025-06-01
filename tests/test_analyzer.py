import pytest
from cybermule.executors import analyzer
from unittest.mock import patch

from cybermule.utils.parsing import extract_first_json_block

# === extract_json_block ===

def test_extract_json_block_valid():
    text = """```json
{
  "file": "src/example.py",
  "line": 10,
  "fix_description": "Fix off-by-one error",
  "code_snippet": "return x + 1"
}
```"""
    result = extract_first_json_block(text)
    assert isinstance(result, dict)
    assert result["file"] == "src/example.py"
    assert result["line"] == 10

def test_extract_json_block_invalid():
    text = """```json
{ invalid json
```"""
    result = extract_first_json_block(text)
    assert result is None

def test_extract_json_block_no_json():
    text = "This is just a string without code blocks"
    result = extract_first_json_block(text)
    assert result is None

# === analyze_failure_with_llm ===

@pytest.fixture
def mock_config():
    return {
        "llm": {
            "provider": "mock",
        },
        "prompt_dir": "/dev/null"  # Not used due to patching
    }

@patch("cybermule.executors.analyzer.get_llm_provider")
@patch("cybermule.executors.analyzer.get_prompt_path")
@patch("cybermule.executors.analyzer.render_template")
def test_analyze_failure_with_llm_mocked(
    mock_render_template,
    mock_get_prompt_path,
    mock_get_llm_provider,
    mock_config
):
    class MockLLM:
        def generate(self, prompt, history=()):
            return """```json
{
  "file": "project/fail.py",
  "line": 17,
  "fix_description": "Add missing import",
  "code_snippet": "import os"
}
```"""

    mock_get_prompt_path.return_value = "/dev/null/fix_traceback.j2"
    mock_render_template.return_value = "fake rendered prompt"
    mock_get_llm_provider.return_value = MockLLM()

    traceback = "Traceback (most recent call last): ..."
    result, _ = analyzer.analyze_failure_with_llm(traceback, mock_config)

    assert result["file"] == "project/fail.py"
    assert result["line"] == 17
    assert "import os" in result["code_snippet"]

# === summarize_traceback ===

@patch("cybermule.executors.analyzer.get_llm_provider")
@patch("cybermule.executors.analyzer.get_prompt_path")
@patch("cybermule.executors.analyzer.render_template")
def test_summarize_traceback_mocked(
    mock_render_template,
    mock_get_prompt_path,
    mock_get_llm_provider,
    mock_config
):
    class MockLLM:
        def generate(self, prompt, history=()):
            return "This error occurred in file test_app.py on line 23 due to a missing argument."

    mock_get_prompt_path.return_value = "/dev/null/summarize_traceback.j2"
    mock_render_template.return_value = "summary prompt"
    mock_get_llm_provider.return_value = MockLLM()

    traceback = "Traceback (most recent call last): ..."
    summary, _ = analyzer.summarize_traceback(traceback, mock_config)

    assert "file" in summary
    assert "line" in summary
    assert "missing argument" in summary
