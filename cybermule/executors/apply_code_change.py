import typer

from typing import Dict, Optional
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.utils.aider_engine import apply_with_aider
from cybermule.utils.config_loader import get_aider_extra_args
from cybermule.utils.git_utils import get_commits_since, get_latest_commit_sha, run_git_command


def apply_code_change(
    change_plan: Dict,
    config: dict,
    graph: Optional[MemoryGraph] = None,
    parent_id: Optional[str] = None,
    operation_type: str = "fix"
) -> Optional[str]:

    if "edits" not in change_plan:
        raise ValueError("[apply_code_change] No edits found in change plan.")

    pre_sha = get_latest_commit_sha()

    message_parts = []
    touched_files = set()

    for edit in change_plan["edits"]:
        file_path = edit["file"]
        touched_files.add(file_path)

        message_parts.append(
            f"In `{file_path}`:\n- {edit.get('fix_description', 'Edit')}\n"
            f"```python\n{edit['code_snippet']}\n```"
        )

    message = "\n\n".join(message_parts)
    file_paths = list(touched_files)

    # Print message for visibility
    typer.echo("[apply_code_change] 📝 Message sent to Aider:")
    typer.echo("=" * 60)
    typer.echo(message)
    typer.echo("=" * 60)

    # NEW: extract CLI args from config
    extra_args = get_aider_extra_args(config)

    success = apply_with_aider(file_paths=file_paths, message=message, extra_args=extra_args)

    if not success:
        typer.echo("[apply_code_change] ❌ Aider failed — rolling back changes.")
        run_git_command(["reset", "--hard", pre_sha])
        typer.echo(f"[apply_code_change] ↩️  Reverted to commit: {pre_sha}")

        raise RuntimeError("[apply_code_change] Aider failed to apply the fix.")
    
    post_shas = get_commits_since(pre_sha)
    
    node_id = None
    if graph:
        node_id = graph.new(f"Apply {operation_type}", parent_id=parent_id,
                            tags=[operation_type])
        graph.update(node_id,
            status="CHANGE_APPLIED",
            fix_description=change_plan.get("fix_description", ""),
            message=message, files=file_paths, commits=post_shas
        )

    typer.echo(f"[apply_code_change] ✅ Fix applied using Aider to {len(file_paths)} file(s).")
    return node_id
