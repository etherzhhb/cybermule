import typer
import json
import os

def run(filename: str):
    if not os.path.exists(filename):
        typer.echo(f"Log file not found: {filename}")
        return
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
        typer.echo(json.dumps(data, indent=2))