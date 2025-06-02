import pytest
from cybermule.executors import analyzer
from unittest.mock import patch


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
        def generate(self, *args, **kwargs):
            return """
<error_summary>
some error happen
</error_summary>
```json
{
    "fix_description": "fix",
    "edits": [
        {
            "file": "project/fail.py",
            "line": 17,
            "fix_description": "Add missing import",
            "code_snippet": "import os"
        }
    ]
}
```"""

    mock_get_prompt_path.return_value = "/dev/null/fix_traceback.j2"
    mock_render_template.return_value = "fake rendered prompt"
    mock_get_llm_provider.return_value = MockLLM()

    traceback = "Traceback (most recent call last): ..."
    result, _ = analyzer.analyze_failure_with_llm(traceback, mock_config)
    edit = result["edits"][0]

    assert edit["file"] == "project/fail.py"
    assert edit["line"] == 17
    assert "import os" in edit["code_snippet"]

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
            return "<error_summary>This error occurred in file test_app.py on line 23 due to a missing argument.</error_summary>"

    mock_get_prompt_path.return_value = "/dev/null/summarize_traceback.j2"
    mock_render_template.return_value = "summary prompt"
    mock_get_llm_provider.return_value = MockLLM()

    traceback = "Traceback (most recent call last): ..."
    summary, _ = analyzer.summarize_traceback(traceback, mock_config)

    assert "file" in summary
    assert "line" in summary
    assert "missing argument" in summary
