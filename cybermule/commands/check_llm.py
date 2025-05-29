import typer
from cybermule.providers.llm_provider import LLMProvider

def run():
    typer.echo("[🔍] Checking LLM provider connection...")
    try:
        llm = LLMProvider()
        response = llm.generate("Say hello")
        typer.echo("[✅] LLM connection successful!")
        typer.echo(f"[🤖] Model response: {response.strip()}")
    except Exception as e:
        typer.echo("[❌] LLM connection failed!")
        typer.echo(str(e))