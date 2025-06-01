from pathlib import Path
from typing import Optional, List
import difflib

import typer
from markdown_it import MarkdownIt

from cybermule.memory.memory_graph import MemoryGraph
from cybermule.providers.llm_provider import get_llm_provider
from cybermule.utils.config_loader import get_prompt_path
from cybermule.utils.file_utils import read_file_content, resolve_context_inputs
from cybermule.utils.template_utils import render_template


def execute(
    graph: Optional[MemoryGraph],
    file: Path,
    goal: str,
    context: Optional[List[str]] = None,
    preview: bool = False,
    config: Optional[dict] = None
) -> str:
    """
    Executes a refactoring operation using an LLM.

    Parameters:
        graph: Optional MemoryGraph for logging node execution. If None, runs standalone.
        file: Path to the file to refactor.
        goal: Description of the refactoring goal (e.g. "extract class").
        context: Optional list of context file globs or paths.
        preview: If True, prints a unified diff instead of applying changes.
        config: Optional configuration dictionary for prompt path and LLM.

    Returns:
        node_id (if graph is provided), or None
    """
    local_graph = graph or MemoryGraph()
    node_id = local_graph.new(f"Refactor {file.name}: {goal}")

    file_text = read_file_content(file)

    # Resolve context files
    context_code = ""
    if context:
        context_files = resolve_context_inputs(context)
        context_parts = [
            f"# File: {cf}\n{read_file_content(cf)}" for cf in context_files
        ]
        context_code = "\n\n".join(context_parts)

    # Prepare prompt
    prompt_path = get_prompt_path(config or {}, name="refactor.j2")
    prompt = render_template(prompt_path, {
        "PYTHON_CODE": file_text,
        "REFACTORING_GOAL": goal,
        "CONTEXT_CODE": context_code
    })

    llm = get_llm_provider(config)
    response = llm.generate(prompt, respond_prefix="<refactoring_analysis>")
    refactored_code = extract_code_blocks(response)[0] if extract_code_blocks(response) else ""

    diff = difflib.unified_diff(
        file_text.splitlines(),
        refactored_code.splitlines(),
        fromfile=str(file),
        tofile=f"{file}.refactored",
        lineterm=""
    )

    diff_txt = "\n".join(diff)
    if preview:
        typer.echo(diff_txt)
        status = "REFACTOR_PREVIEWED"
    else:
        file.write_text(refactored_code)
        status="REFACTORED"
  
    local_graph.update(node_id, prompt=prompt, response=response,
                       original_code=file_text, context_code=context_code,
                       generated_code=refactored_code, diff=diff_txt,
                       goal=goal, status=status)
    return node_id if graph else None


def extract_code_blocks(text: str) -> List[str]:
    md = MarkdownIt()
    tokens = md.parse(text)
    return [
        t.content for t in tokens
        if t.type == "fence" and t.info.strip() in ("python", "")
    ]
