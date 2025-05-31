import typer
from pathlib import Path
import difflib
import jinja2
from markdown_it import MarkdownIt
from typing import List, Optional

from cybermule.providers.llm_provider import get_llm_provider
from cybermule.tools.config_loader import get_prompt_path
from cybermule.utils.file_utils import read_file_content

def run(
    ctx: typer.Context,
    file: Path = typer.Argument(..., exists=True, help="Path to the file to refactor"),
    goal: str = typer.Option(..., help="Refactoring goal, e.g., 'extract class', 'rename variable'"),
    preview: bool = typer.Option(False, help="Show diff instead of applying changes"),
    context_files: Optional[List[Path]] = typer.Option(
        None, 
        "--context", 
        "-c", 
        help="Additional files to provide context for refactoring",
        exists=True
    ),
):    
    config = ctx.obj["config"]

    typer.echo(f"🛠️  Refactoring {file} with goal: '{goal}'")
    file_text = read_file_content(file)
    
    # Process context files if provided
    context_code = ""
    if context_files:
        context_parts = []
        for context_file in context_files:
            content = read_file_content(context_file)
            if content:
                context_parts.append(f"# File: {context_file.name}\n{content}")
        
        if context_parts:
            context_code = "\n\n".join(context_parts)
            typer.echo(f"📚 Added {len(context_files)} context file(s)")

    # Load and render the template
    prompt_path = Path(__file__).parent.parent / get_prompt_path(config, name="refactor.j2")
    template_vars = {
        "PYTHON_CODE": file_text,
        "REFACTORING_GOAL": goal,
        "CONTEXT_CODE": context_code
    }
    prompt = render_template(prompt_path, template_vars)

    if ctx.obj["debug_prompt"]:
        typer.echo("\n--- Refactor Prompt ---\n" + prompt + "\n--- End Prompt ---\n")

    llm = get_llm_provider(config)
    response = llm.generate(prompt, partial_assistant_response="<refactoring_analysis>")

    if ctx.obj["debug_prompt"]:
        typer.echo("\n--- Refactor Respond ---\n" + response + "\n--- End Respond ---\n")

    refactored_code, = extract_code_blocks(response)

    if preview:
        diff = difflib.unified_diff(
            file_text.splitlines(),
            refactored_code.splitlines(),
            fromfile=str(file),
            tofile=f"{file}.refactored",
            lineterm=""
        )
        typer.echo("\n".join(diff))
        return

    file.write_text(refactored_code)
    typer.echo(f"✅ Refactoring complete.")

def extract_code_blocks(text):
    md = MarkdownIt()
    tokens = md.parse(text)
    return [
        t.content for t in tokens
        if t.type == "fence" and t.info.strip() in ("python", "")
    ]
