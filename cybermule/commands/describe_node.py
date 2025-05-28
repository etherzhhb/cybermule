import typer
from tools.memory_graph import MemoryGraph

def run(node_id: str):
    graph = MemoryGraph()

    matches = [node for node in graph.list() if node['id'].startswith(node_id)]
    if not matches:
        typer.echo(f"No node found with ID starting with '{node_id}'")
        return
    if len(matches) > 1:
        typer.echo(f"Multiple matches for '{node_id}':")
        for node in matches:
            typer.echo(f"- {node['id'][:6]}: {node['task']}")
        return

    node = matches[0]
    typer.echo(f"🔍 Node ID: {node['id']}")
    typer.echo(f"📝 Task: {node.get('task', '')}")
    typer.echo(f"📌 Status: {node.get('status', 'UNKNOWN')}")
    if node.get("parent"):
        typer.echo(f"↖️  Parent: {node['parent']}")
    if node.get("children"):
        typer.echo(f"↘️  Children: {', '.join(node['children'])}")

    typer.echo("\n📤 Prompt:\n" + node.get("prompt", "").strip()[:1000] + "...")
    typer.echo("\n📥 Response:\n" + node.get("response", "").strip()[:1000] + "...")
    if node.get("error"):
        typer.echo("\n❌ Error:\n" + node["error"].strip()[:1000] + "...")