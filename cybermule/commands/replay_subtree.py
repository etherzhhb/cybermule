from pathlib import Path
import typer
import yaml

from cybermule.executors.llm_replay import replay_subtree
from cybermule.memory.memory_graph import MemoryGraph

def run(
    ctx: typer.Context,
    node_id: str = typer.Argument(..., help="Root node ID to replay"),
    graph_path: Path = typer.Option("memory_graph.json", help="Path to the memory graph file"),
    prompt_map: Path = typer.Option(None, help="YAML file with prompt substitution map"),
):
    """
    Replay a subtree of LLM tasks from a given root node.
    """
    config = ctx.obj["config"]

    graph = MemoryGraph(storage_path=graph_path)

    substitutions = {}
    if prompt_map:
        with open(prompt_map) as f:
            substitutions = yaml.safe_load(f)

    node_id_map = replay_subtree(
        root_node_id=node_id,
        graph=graph,
        config=config,
        prompt_substitutions=substitutions,
    )

    typer.echo(f"🔁 [replay_subtree] Replayed {len(node_id_map)} nodes:")
    for original, new in node_id_map.items():
        typer.echo(f"  {original} → {new}")
