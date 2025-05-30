import typer
from cybermule.providers.llm_provider import get_llm_provider

def run(ctx: typer.Context):
    typer.echo("[🔍] Checking LLM provider connection...")
    try:
        llm = get_llm_provider(ctx.obj["config"])
        response = llm.generate("Say hello and identify yourself")
        typer.echo("[✅] LLM connection successful!")
        typer.echo(f"[🤖] Model response: {response.strip()}")
    except Exception as e:
        typer.echo("[❌] LLM connection failed!")
        typer.echo(str(e))