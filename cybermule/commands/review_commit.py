import typer
from cybermule.providers.llm_provider import get_llm_provider
from cybermule.tools.config_loader import get_prompt_path
from cybermule.utils import git_utils
from cybermule.memory.memory_graph import MemoryGraph
from langchain.prompts import PromptTemplate
from pathlib import Path

def run(ctx: typer.Context,
        sha: str = typer.Option(None, help="Commit SHA to review (default: latest)"),
        fetch: str = typer.Option(None, help="Git remote to fetch before reviewing")):
    if fetch:
        typer.echo(f"📡 Fetching from remote '{fetch}'...")
        git_utils.fetch_remote(fetch)

    commit_sha = sha or git_utils.get_latest_commit_sha()
    commit_msg = git_utils.get_commit_message_by_sha(commit_sha)
    commit_diff = git_utils.get_commit_diff_by_sha(commit_sha)

    task = f"Review commit {commit_sha[:7]}"
    graph = MemoryGraph()
    node_id = graph.new(task)

    config = ctx.obj["config"]
    prompt_path = get_prompt_path(config, name="review_git_commit.prompt")
    prompt_template = PromptTemplate.from_template(prompt_path.read_text())
    prompt = prompt_template.format(commit_message=commit_msg, commit_diff=commit_diff)

    if ctx.obj["debug_prompt"]:
        typer.echo("\n--- Review Commit Prompt ---\n" + prompt + "\n--- End Prompt ---\n")

    llm = get_llm_provider(config)
    review = llm.generate(prompt)

    typer.echo(f"🔍 Commit SHA: {commit_sha}\n")
    typer.echo("📋 AI Review:\n")
    typer.echo(review)

    graph.update(node_id, prompt=prompt, response=review, status="REVIEWED")