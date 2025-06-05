import pytest
from unittest.mock import patch, MagicMock
from cybermule.executors.apply_code_change import apply_code_change

fake_plan = {
    "fix_description": "Refactor function",
    "edits": [
        {
            "file": "some_file.py",
            "fix_description": "Update return value",
            "code_snippet": "def foo():\n    return 42"
        }
    ]
}


@patch("cybermule.executors.apply_code_change.apply_with_aider", return_value=True)
@patch("cybermule.executors.apply_code_change.get_commits_since", return_value=["newsha123"])
@patch("cybermule.executors.apply_code_change.get_latest_commit_sha", return_value="oldsha000")
def test_apply_success(mock_sha, mock_commits, mock_aider):
    mock_graph = MagicMock()
    node_id = apply_code_change(fake_plan, config={}, graph=mock_graph, operation_type="refactor")
    
    assert node_id is not None
    mock_aider.assert_called_once()
    mock_graph.new.assert_called_once()
    mock_graph.update.assert_called_once()


@patch("cybermule.executors.apply_code_change.apply_with_aider", return_value=False)
@patch("cybermule.executors.apply_code_change.get_latest_commit_sha", return_value="oldsha000")
@patch("cybermule.executors.apply_code_change.run_git_command")
def test_apply_failure_rolls_back(mock_git, mock_sha, mock_aider):
    with pytest.raises(RuntimeError):
        apply_code_change(fake_plan, config={}, graph=None)

    mock_git.assert_called_with(["reset", "--hard", "oldsha000"])


def test_missing_edits_raises():
    with pytest.raises(ValueError):
        apply_code_change({}, config={})
