import typer
from cybermule.providers.llm_provider import ClaudeBedrockProvider
from cybermule.tools import code_generator, test_runner, code_indexer
from cybermule.tools.memory_graph import MemoryGraph
from cybermule.tools.config_loader import get_prompt_path
from pathlib import Path
from langchain.prompts import PromptTemplate

def load_template(name: str) -> str:
    path = Path(__file__).parent.parent / get_prompt_path(name)
    return path.read_text(encoding="utf-8")

def run(debug_prompt: bool = typer.Option(False, help='Print rendered prompt before calling LLM')):
    claude = ClaudeBedrockProvider()
    graph = MemoryGraph()
    task = typer.prompt("What do you want the agent to do?")

    node_id = graph.new(task)
    indexer = code_indexer.CodeIndexer()

    for fname in ["generated_code.py"]:
        try:
            indexer.add_file(fname)
        except FileNotFoundError:
            pass

    context_snippets = indexer.search(task)
    combined_context = "\n\n".join([code for _, code in context_snippets])

    template_str = load_template("generate_code.j2")
    prompt = PromptTemplate.from_template(template_str)
    rendered = prompt.format(task=task, context=combined_context)

    if debug_prompt:
        typer.echo("\n--- Rendered Prompt ---\n" + rendered + "\n--- End Prompt ---\n")

    code = claude.generate(rendered)
    graph.update(node_id, prompt=rendered, response=code)

    with open("generated_code.py", "w", encoding="utf-8") as f:
        f.write(code)

    typer.echo("Generated Code:\n" + code)

    stdout, stderr = test_runner.run_pytest()
    graph.update(node_id, status="PASSED" if "FAILED" not in stdout and "error:" not in stderr else "FAILED", error=stderr)

    if "FAILED" in stdout or "error:" in stderr:
        typer.echo("\nRetrying with feedback...\n")
        retry_id = graph.new("Retry after failure", parent_id=node_id)

        template_str = load_template("fix_code_error.j2")
        fix_prompt = PromptTemplate.from_template(template_str)
        rendered = fix_prompt.format(original_code=code, error_output=stderr)

        if debug_prompt:
            typer.echo("\n--- Fix Prompt ---\n" + rendered + "\n--- End Fix Prompt ---\n")

        fixed_code = claude.generate(rendered)
        graph.update(retry_id, prompt=rendered, response=fixed_code)

        with open("generated_code.py", "w", encoding="utf-8") as f:
            f.write(fixed_code)

        typer.echo("Fixed Code:\n" + fixed_code)

        stdout, stderr = test_runner.run_pytest()
        graph.update(retry_id, status="PASSED" if "FAILED" not in stdout and "error:" not in stderr else "FAILED", error=stderr)

    typer.echo("Session saved to memory graph.")