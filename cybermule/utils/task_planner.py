# cybermule/utils/task_planner.py

import typer
from pathlib import Path


def ask_for_context() -> list[str]:
    if typer.confirm("Do you want to provide context files/directories?", default=False):
        raw_input = typer.prompt("🗂️ Enter paths (space-separated)")
        return [p for p in raw_input.split() if p.strip()]
    return []

def summarize_plan(plan: dict):
    typer.echo("\n📣 Here's what I understood:")
    if plan["mode"] == "generate":
        typer.echo(f"  → Generate task: {plan['goal']}")
        typer.echo(f"  → Target file: {plan['file']}")
    else:
        typer.echo(f"  → Refactor file: {plan['file']}")
        typer.echo(f"  → Goal: {plan['goal']}")
    typer.echo(f"  → Context files: {', '.join(plan['context']) if plan['context'] else 'none'}")


def plan_generate_or_refactor() -> dict:
    """
    Interactive prompt to collect a 'generate' or 'refactor' task.
    Returns:
    {
        "mode": "generate" | "refactor",
        "goal": str,
        "file": Path,
        "context": List[str]
    }
    """
    mode = typer.prompt("What kind of task? (generate/refactor)").strip().lower()
    while mode not in ("generate", "refactor"):
        typer.echo("❌ Please enter either 'generate' or 'refactor'")
        mode = typer.prompt("What kind of task? (generate/refactor)").strip().lower()

    plan = {"mode": mode}

    if mode == "generate":
        plan["goal"] = typer.prompt("🧠 What do you want to generate?")
        plan["file"] = Path(typer.prompt("📄 Where should the generated code be saved? (e.g. my_script.py)"))
    else:
        file_path = Path(typer.prompt("📂 Which file do you want to refactor?"))
        if not file_path.exists():
            typer.echo(f"❌ File not found: {file_path}")
            raise typer.Exit(code=1)
        plan["file"] = file_path
        plan["goal"] = typer.prompt("🎯 What is your refactoring goal?\n(e.g. 'extract class Foo')")

    plan["context"] = ask_for_context()
    summarize_plan(plan)

    if not typer.confirm("Shall I proceed?", default=True):
        raise typer.Exit()

    return plan
