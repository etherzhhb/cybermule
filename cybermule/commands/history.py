import typer
from cybermule.memory.memory_graph import MemoryGraph

def run():
    graph = MemoryGraph()
    nodes = graph.list()

    if not nodes:
        typer.echo("No memory nodes found.")
        return

    for node in nodes:
        nid = node['id'][:6]
        task = node.get("task", "")[:40]
        status = node.get("status", "UNKNOWN")
        parent = node.get("parent")
        children = node.get("children", [])
        parent_info = f" ← {parent[:6]}" if parent else ""
        child_info = f" → {len(children)} child{'ren' if len(children) != 1 else ''}" if children else ""
        status_symbol = "✅" if status == "PASSED" else ("❌" if status == "FAILED" else "🟡")
        typer.echo(f"[{nid}] {task} — {status_symbol} {status}{parent_info}{child_info}")