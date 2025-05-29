import typer
from cybermule.providers.llm_provider import get_llm_provider
from cybermule.tools.config_loader import get_prompt_path
from cybermule.tools import git_utils
from cybermule.tools.memory_graph import MemoryGraph
from langchain.prompts import PromptTemplate
from pathlib import Path

def run(debug_prompt: bool = typer.Option(False, help="Print the rendered prompt before sending to LLM")):
    commit_sha = git_utils.get_latest_commit_sha()
    commit_msg = git_utils.get_latest_commit_message()
    commit_diff = git_utils.get_latest_commit_diff()

    task = f"Review commit {commit_sha[:7]}"
    graph = MemoryGraph()
    node_id = graph.new(task)

    prompt_path = Path(__file__).parent.parent / get_prompt_path("review_git_commit.j2")
    prompt_template = PromptTemplate.from_template(prompt_path.read_text())
    prompt = prompt_template.format(commit_message=commit_msg, commit_diff=commit_diff)

    if debug_prompt:
        typer.echo("\n--- Review Commit Prompt ---\n" + prompt + "\n--- End Prompt ---\n")

    llm = get_llm_provider()
    review = llm.generate(prompt)

    typer.echo(f"🔍 Commit SHA: {commit_sha}\n")
    typer.echo("📋 AI Review:\n")
    typer.echo(review)

    graph.update(node_id, prompt=prompt, response=review, status="REVIEWED")