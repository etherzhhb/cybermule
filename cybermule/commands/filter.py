import typer
import json
import os

def run(keyword: str = "", mode: str = "", date: str = ""):
    logs = [f for f in os.listdir(".") if f.startswith("session_") and f.endswith(".json")]
    found = False
    for log in sorted(logs):
        try:
            with open(log, "r", encoding="utf-8") as f:
                data = json.load(f)
                content = json.dumps(data).lower()
                if keyword and keyword.lower() not in content:
                    continue
                if mode and data.get("mode") != mode:
                    continue
                if date and not data.get("timestamp", "").startswith(date):
                    continue
                typer.echo(f"Match in: {log}")
                found = True
        except Exception:
            continue
    if not found:
        typer.echo("No logs matched the given filters.")