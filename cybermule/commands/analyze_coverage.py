import json
import typer
from pathlib import Path
from langchain.prompts import PromptTemplate
from cybermule.providers.llm_provider import get_llm_provider
from cybermule.tools.config_loader import get_prompt_path

def run(file: str, debug_prompt: bool = typer.Option(False, help="Print rendered prompt before sending to LLM")):
    coverage_path = Path("coverage.json")
    if not coverage_path.exists():
        typer.echo("❌ coverage.json not found. Run 'coverage run -m pytest && coverage json' first.")
        raise typer.Exit(1)

    data = json.loads(coverage_path.read_text())
    filename = Path(file).resolve()

    matched_file = None
    for source_file, meta in data.get("files", {}).items():
        if Path(source_file).resolve() == filename:
            matched_file = meta
            break

    if not matched_file:
        typer.echo(f"❌ File '{file}' not found in coverage report.")
        raise typer.Exit(1)

    uncovered = matched_file["missing_lines"]
    if not uncovered:
        typer.echo("✅ No uncovered lines found!")
        return

    source = Path(file).read_text()
    uncovered_str = ", ".join(str(line) for line in uncovered)

    prompt_path = get_prompt_path("suggest_test_cases.j2")
    template = PromptTemplate.from_template(prompt_path.read_text())
    prompt = template.format(source_code=source, uncovered_lines=uncovered_str)

    if debug_prompt:
        typer.echo("\n--- Test Suggestion Prompt ---\n" + prompt + "\n--- End Prompt ---\n")

    llm = get_llm_provider()
    suggestions = llm.generate(prompt)

    typer.echo("🧪 Suggested Tests:\n")
    typer.echo(suggestions)