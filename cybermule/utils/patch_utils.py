from pathlib import Path
from typing import Dict, Optional
import difflib
from cybermule.memory.memory_graph import MemoryGraph

def apply_fix(
    fix_plan: Dict,
    graph: Optional[MemoryGraph] = None,
    parent_id: Optional[str] = None
) -> Optional[str]:
    """
    Applies a multi-edit code fix plan.

    Behavior:
    - If line_start == line_end: insert before that line
    - If line_start < line_end: replace the inclusive line range

    Args:
        fix_plan: Dict with keys 'fix_description' and 'edits' (list of edit dicts)
        graph: Optional MemoryGraph for logging
        parent_id: Optional node ID to attach this operation to

    Returns:
        node_id (if graph is provided), else None
    """
    if "edits" not in fix_plan:
        raise ValueError("[apply_fix] No edits found in fix plan.")

    node_id = None
    log_entries = []

    for edit in fix_plan["edits"]:
        file_path = Path(edit["file"])
        line_start = edit["line_start"]
        line_end = edit["line_end"]
        code_snippet = edit["code_snippet"]

        if not file_path.exists():
            raise FileNotFoundError(f"[apply_fix] File not found: {file_path}")

        lines = file_path.read_text(encoding="utf-8").splitlines()

        if line_start < 1 or line_start > len(lines) + 1:
            raise IndexError(f"[apply_fix] line_start {line_start} out of bounds in {file_path}")

        original_lines = []
        updated_lines = code_snippet.splitlines()

        if line_start == line_end:
            # Insertion before line_start
            lines[line_start - 1:line_start - 1] = updated_lines
        else:
            if line_end > len(lines):
                raise IndexError(f"[apply_fix] line_end {line_end} out of bounds in {file_path}")
            original_lines = lines[line_start - 1:line_end]
            lines[line_start - 1:line_end] = updated_lines

        updated_text = "\n".join(lines) + "\n"
        file_path.write_text(updated_text, encoding="utf-8")

        diff = "\n".join(difflib.unified_diff(
            original_lines,
            updated_lines,
            fromfile=f"{file_path} (original)",
            tofile=f"{file_path} (patched)",
            lineterm=""
        ))

        log_entries.append({
            "file": str(file_path),
            "line_start": line_start,
            "line_end": line_end,
            "diff": diff
        })

    if graph:
        node_id = graph.new("Apply fix", parent_id=parent_id, tags=["apply"])
        graph.update(node_id,
            status="FIX_APPLIED",
            fix_description=fix_plan.get("fix_description", ""),
            edits=log_entries
        )

    print(f"[apply_fix] ✅ Applied {len(fix_plan['edits'])} edits across {len(set(e['file'] for e in fix_plan['edits']))} file(s)")
    return node_id
