import typer
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.providers.llm_provider import get_llm_provider
from cybermule.utils.config_loader import get_prompt_path
from langchain.prompts import PromptTemplate
from cybermule.executors import run_codegen, run_tests, fix_errors, suggest_tests

executor_map = {
    "run_codegen": run_codegen.execute,
    "run_tests": run_tests.execute,
    "fix_errors": fix_errors.execute,
    "suggest_tests": suggest_tests.execute,
}

def classify_executor(desc: str) -> str:
    prompt_path = get_prompt_path("classify_step.j2")
    prompt_template = PromptTemplate.from_template(Path(prompt_path).read_text())
    prompt = prompt_template.format(step_description=desc)
    llm = get_llm_provider()
    label = llm.generate(prompt).strip()
    return label

def run(plan_node_id: str = typer.Argument(..., help="Node ID of the plan"),
        source_file: str = typer.Option(..., help="Source file for coverage-based test suggestions"),
        debug: bool = typer.Option(False, help="Enable prompt and output debug printing")):

    graph = MemoryGraph()

    if plan_node_id not in graph.data:
        raise typer.BadParameter(f"Node {plan_node_id} not found.")

    step_ids = [nid for nid, n in graph.data.items() if n.get("parent") == plan_node_id]
    step_ids.sort()

    for nid in step_ids:
        desc = graph.data[nid]["task"]

        try:
            executor_name = classify_executor(desc)
            if debug:
                typer.echo(f"[classify] {desc.strip()} → {executor_name}")
            if executor_name not in executor_map:
                typer.echo(f"[!] Unknown executor: {executor_name}")
                continue

            # Pass source_file if needed
            if executor_name == "suggest_tests":
                executor_map[executor_name](graph, source_file=source_file)
            elif executor_name == "fix_errors":
                executor_map[executor_name](graph, parent_node_id=nid)
            else:
                executor_map[executor_name](graph, task_description=desc)
        except Exception as e:
            typer.echo(f"[!] Failed to classify or run step: {desc}\n{e}")

    typer.echo("\n✅ Planner loop complete. Use `history` or `describe-node` to review.")

    # Task Completion Check
    try:
        plan_node = graph.data[plan_node_id]
        task_description = plan_node.get("task") or plan_node.get("title") or "Unknown task"

        steps = [graph.data[nid] for nid in step_ids]
        history_summary = "\n".join(
            f"Step: {s.get('task', 'unknown')}\nResult: {s.get('response', '')[:300]}" for s in steps
        )

        prompt_path = get_prompt_path("task_done.j2")
        prompt_template = PromptTemplate.from_template(Path(prompt_path).read_text())
        prompt = prompt_template.format(task_description=task_description, history=history_summary)

        llm = get_llm_provider()
        result = llm.generate(prompt).strip().upper()

        typer.echo(f"\n📌 Task completion decision: {result}")
        if result.startswith("YES"):
            typer.echo("✅ Task marked as complete.")
        elif result.startswith("NO"):
            typer.echo("🔁 Task may require additional work.")
        else:
            typer.echo("⚠️ Unexpected result format from task_done.j2")
    
            # Auto self-correct if tests failed
            if executor_name == "run_tests" and "FAIL" in graph.data[nid].get("response", ""):
                typer.echo("[!] Test failed. Attempting self-correction...")
                import commands.self_correct as self_correct
                self_correct.run(node_id=nid, file=source_file, max_retries=2)
    except Exception as e:
        typer.echo(f"[!] Could not check task completion: {e}")
