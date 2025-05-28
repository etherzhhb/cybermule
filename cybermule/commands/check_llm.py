import typer
from providers.llm_provider import ClaudeBedrockProvider

def run():
    typer.echo("[🔍] Checking LLM provider connection...")
    try:
        llm = ClaudeBedrockProvider()
        response = llm.generate("Say hello")
        typer.echo("[✅] LLM connection successful!")
        typer.echo(f"[🤖] Model response: {response.strip()}")
    except Exception as e:
        typer.echo("[❌] LLM connection failed!")
        typer.echo(str(e))