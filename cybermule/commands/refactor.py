import typer
from pathlib import Path
import difflib
from langchain.prompts import PromptTemplate

from cybermule.providers.llm_provider import get_llm_provider
from cybermule.tools.config_loader import get_prompt_path

def run(
    ctx: typer.Context,
    file: Path = typer.Argument(..., exists=True, help="Path to the file to refactor"),
    goal: str = typer.Option(..., help="Refactoring goal, e.g., 'extract class', 'rename variable'"),
    preview: bool = typer.Option(False, help="Show diff instead of applying changes"),
):    
    config = ctx.obj["config"]

    typer.echo(f"🛠️  Refactoring {file} with goal: '{goal}'")
    file_text = file.read_text()

    prompt_path = Path(__file__).parent.parent / get_prompt_path(config, name="refactor.prompt")
    prompt_template = PromptTemplate.from_template(prompt_path.read_text())
    prompt = prompt_template.format(PYTHON_CODE=file_text, REFACTORING_GOAL=goal)

    if ctx.obj["debug_prompt"]:
        typer.echo("\n--- Refactor Prompt ---\n" + prompt + "\n--- End Prompt ---\n")

    llm = get_llm_provider(config)
    response = llm.generate(prompt)

    if ctx.obj["debug_prompt"]:
        typer.echo("\n--- Refactor Respond ---\n" + response + "\n--- End Respond ---\n")

    if preview:
        diff = difflib.unified_diff(
            file_text.splitlines(),
            response.splitlines(),
            fromfile=str(file),
            tofile=f"{file}.refactored",
            lineterm=""
        )
        typer.echo("\n".join(diff))
    else:
        backup = file.with_suffix(file.suffix + ".bak")
        file.rename(backup)
        file.write_text(response)
        typer.echo(f"✅ Refactoring complete. Original backed up to {backup}")
