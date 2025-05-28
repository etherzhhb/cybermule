import typer
from tools.memory_graph import MemoryGraph
from tools.config_loader import get_prompt_path
from providers.llm_provider import ClaudeBedrockProvider
from tools import test_runner
from pathlib import Path
from langchain.prompts import PromptTemplate

def load_template(name: str) -> str:
    path = Path(__file__).parent.parent / get_prompt_path(name)
    return path.read_text(encoding="utf-8")

def run(node_id: str, debug_prompt: bool = typer.Option(False, help="Print rendered fix prompt before calling LLM")):
    graph = MemoryGraph()
    claude = ClaudeBedrockProvider()

    matches = [n for n in graph.list() if n["id"].startswith(node_id)]
    if not matches:
        typer.echo(f"No node found with ID starting with '{node_id}'")
        return
    if len(matches) > 1:
        typer.echo(f"Multiple matches found for '{node_id}':")
        for node in matches:
            typer.echo(f"- {node['id'][:6]}: {node['task']}")
        return

    node = matches[0]
    if not node.get("response") or not node.get("error"):
        typer.echo("Selected node has no code or error trace to retry.")
        return

    retry_id = graph.new("Retry of " + node["task"], parent_id=node["id"])
    template_str = load_template("fix_code_error.j2")
    template = PromptTemplate.from_template(template_str)
    rendered = template.format(original_code=node["response"], error_output=node["error"])

    if debug_prompt:
        typer.echo("\n--- Retry Fix Prompt ---\n" + rendered + "\n--- End Prompt ---\n")

    fixed_code = claude.generate(rendered)
    graph.update(retry_id, prompt=rendered, response=fixed_code)

    with open("generated_code.py", "w", encoding="utf-8") as f:
        f.write(fixed_code)

    typer.echo("🔁 Retried code written to generated_code.py")

    stdout, stderr = test_runner.run_pytest()
    status = "PASSED" if "FAILED" not in stdout and "error:" not in stderr else "FAILED"
    graph.update(retry_id, status=status, error=stderr)

    typer.echo(f"✅ Retry complete. Status: {status}")