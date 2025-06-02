import typer
from cybermule.executors.git_review import review_commit_with_llm

def run(ctx: typer.Context,
        sha: str = typer.Option(None, help="Commit SHA to review (default: latest)"),
        fetch: str = typer.Option(None, help="Git remote to fetch before reviewing")):

    config = ctx.obj["config"]
    review, _ = review_commit_with_llm(config, sha=sha, fetch=fetch)

    typer.echo(f"🔍 Commit SHA: {sha or 'latest'}\n")
    typer.echo("📋 AI Review:\n")
    typer.echo(review)
