import pytest
from pathlib import Path
from cybermule.executors import analyzer
from unittest.mock import patch

from cybermule.memory.memory_graph import MemoryGraph


@pytest.fixture
def mock_config():
    return {
        "llm": {
            "provider": "mock",
        },
        "prompt_dir": "/dev/null"  # Not used due to patching
    }

@patch("cybermule.memory.tracker.get_llm_provider")
@patch("cybermule.memory.tracker.get_prompt_path")
@patch("cybermule.memory.tracker.render_template")
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
some error happened
</error_summary>
```json
{
  "fix_description": "Fix import issue",
  "edits": [
    {
      "file": "project/fail.py",
      "symbol": "main",
      "fix_description": "Add missing import for os module",
      "justification": "The function uses os but it is not imported"
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
    assert edit["symbol"] == "main"
    assert edit["fix_description"] == "Add missing import for os module"
    assert edit["justification"] == "The function uses os but it is not imported"

# === summarize_traceback ===

@patch("cybermule.memory.tracker.get_llm_provider")
@patch("cybermule.memory.tracker.get_prompt_path")
@patch("cybermule.memory.tracker.render_template")
def test_summarize_traceback_mocked(
    mock_render_template,
    mock_get_prompt_path,
    mock_get_llm_provider,
    mock_config
):
    class MockLLM:
        def generate(self, prompt, history=(), respond_prefix=''):
            return "<error_summary>This error occurred in file test_app.py on line 23 due to a missing argument.</error_summary>"

    mock_get_prompt_path.return_value = "/dev/null/summarize_traceback.j2"
    mock_render_template.return_value = "summary prompt"
    mock_get_llm_provider.return_value = MockLLM()

    traceback = "Traceback (most recent call last): ..."
    summary, _ = analyzer.summarize_traceback(traceback, mock_config)

    assert "file" in summary
    assert "line" in summary
    assert "missing argument" in summary

@patch("cybermule.memory.tracker.get_llm_provider")
@patch("cybermule.memory.tracker.get_prompt_path")
@patch("cybermule.memory.tracker.render_template")
def test_fix_plan_with_context_request(
    mock_render_template,
    mock_get_prompt_path,
    mock_get_llm_provider,
    mock_config
):
    class MockLLM:
        def __init__(self):
            self.call_count = 0

        def generate(self, *args, **kwargs):
            self.call_count += 1
            if self.call_count == 1:
                return '''
```json
{
  "needs_more_context": true,
  "request_description": "I need to see helper function",
  "required_info": [
    {
      "code_context_id": "project/fail.py:20",
      "symbol": "helper"
    }
  ]
}
```'''
            
            return '''
```json
{
  "fix_description": "Fix helper bug",
  "edits": [
    {
      "file": "project/fail.py",
      "symbol": "helper",
      "fix_description": "Patch the return logic",
      "justification": "Logic was incorrect"
    }
  ]
}
```'''

    mock_get_prompt_path.return_value = "/dev/null/generate_fix_from_summary.j2"
    mock_render_template.return_value = "fix prompt"
    mock_get_llm_provider.return_value = MockLLM()

    # This triggers the multi-round flow
    traceback = "Traceback (most recent call last): ..."
    error_summary = "some bug occurred"

    from cybermule.executors.analyzer import generate_fix_from_summary
    from cybermule.memory.memory_graph import MemoryGraph

    fix, _ = generate_fix_from_summary(
        error_summary=error_summary,
        traceback=traceback,
        config=mock_config,
        graph=MemoryGraph(),
        parent_id=None,
        max_rounds=3
    )

    assert fix["fix_description"] == "Fix helper bug"
    assert fix["edits"][0]["symbol"] == "helper"


@patch("cybermule.memory.tracker.get_llm_provider")
@patch("cybermule.memory.tracker.get_prompt_path")
@patch("cybermule.memory.tracker.render_template")
def test_fix_plan_multi_round_retry(
    mock_render_template,
    mock_get_prompt_path,
    mock_get_llm_provider
):
    class MockLLM:
        def __init__(self):
            self.call_count = 0

        def generate(self, *args, **kwargs):
            self.call_count += 1
            if self.call_count == 1:
                return '''```json
{
  "needs_more_context": true,
  "request_description": "I need to see helper function",
  "required_info": [
    {
      "symbol": "helper",
      "imported_from": "project/fail.py",
      "ref_path": "project/runner.py",
      "ref_function": "main",
      "lineno": 42
    }
  ]
}
```'''
            else:
                return '''```json
{
  "fix_description": "Fix helper bug",
  "edits": [
    {
      "file": "project/fail.py",
      "symbol": "helper",
      "fix_description": "Patch the return logic",
      "justification": "Logic was incorrect"
    }
  ]
}
```'''

    mock_get_prompt_path.return_value = "/dev/null/generate_fix_from_summary.j2"
    mock_render_template.return_value = "fake rendered prompt"
    mock_get_llm_provider.return_value = MockLLM()

    traceback = "Traceback (most recent call last): ..."
    error_summary = "ValueError in helper"

    fix, _ = analyzer.generate_fix_from_summary(
        error_summary=error_summary,
        traceback=traceback,
        config={"project_root": "."},
        graph=MemoryGraph(),
        parent_id=None,
        max_rounds=3
    )

    assert fix["fix_description"] == "Fix helper bug"
    assert fix["edits"][0]["symbol"] == "helper"
    assert fix["edits"][0]["file"] == "project/fail.py"

@pytest.mark.parametrize("lineno_value,expected", [
    (None, None),
    (42, 42),
    ('42', 42),
    ("around line 42", None),
])
def test_fulfill_context_requests_lineno_handling(lineno_value, expected):
    """Test that fulfill_context_requests handles different lineno values correctly."""
    from cybermule.executors.analyzer import fulfill_context_requests
    
    # Create a minimal required_info with the test lineno value
    required_info = [{
        "symbol": "test_symbol",
        "lineno": lineno_value
    }]
    
    # Mock the symbol resolution functions to avoid actual file system access
    with patch("cybermule.executors.analyzer.resolve_symbol") as mock_resolve:
        # Make resolve_symbol return a valid result
        mock_resolve.return_value = {
            "file": "test_file.py",
            "symbol": "test_symbol",
            "snippet": "def test_symbol(): pass",
            "start_line": 10
        }
        
        # This should not raise an exception for the test cases
        results = fulfill_context_requests(required_info, Path("."))
        
        # Verify the lineno was processed correctly
        if expected is None:
            assert results[0]["traceback_line"] == 10  # Should fall back to start_line
        else:
            assert results[0]["traceback_line"] == expected


@patch("cybermule.memory.tracker.get_llm_provider")
@patch("cybermule.memory.tracker.get_prompt_path")
@patch("cybermule.memory.tracker.render_template")
def test_fix_plan_max_rounds_exceeded(
    mock_render_template,
    mock_get_prompt_path,
    mock_get_llm_provider
):
    class MockLLM:
        def generate(self, *args, **kwargs):
            return '''```json
{
  "needs_more_context": true,
  "request_description": "Still not enough",
  "required_info": [
    {
      "symbol": "unknown_func",
      "imported_from": "project/mystery.py",
      "ref_path": "project/unknown.py",
      "ref_function": "main"
    }
  ]
}
```'''

    mock_get_prompt_path.return_value = "/dev/null/generate_fix_from_summary.j2"
    mock_render_template.return_value = "fake rendered prompt"
    mock_get_llm_provider.return_value = MockLLM()

    traceback = "Traceback (most recent call last): ..."
    error_summary = "Still unclear after 3 rounds"

    fix, _ = analyzer.generate_fix_from_summary(
        error_summary=error_summary,
        traceback=traceback,
        config={"project_root": "."},
        graph=MemoryGraph(),
        parent_id=None,
        max_rounds=3
    )

    assert fix.get("needs_more_context") is True
    assert "required_info" in fix
