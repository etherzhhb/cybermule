import json
from pathlib import Path
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.providers.llm_provider import get_llm_provider
from cybermule.tools.config_loader import get_prompt_path
from langchain.prompts import PromptTemplate

def execute(graph: MemoryGraph, source_file: str, debug_prompt: bool = False) -> str:
    node_id = graph.new(f"Suggest tests for uncovered code in {source_file}")

    # Load coverage.json
    coverage_path = Path("coverage.json")
    if not coverage_path.exists():
        raise RuntimeError("coverage.json not found. Run: coverage run -m pytest && coverage json")

    data = json.loads(coverage_path.read_text())
    file_path = Path(source_file).resolve()

    matched = None
    for src, meta in data.get("files", {}).items():
        if Path(src).resolve() == file_path:
            matched = meta
            break

    if not matched:
        raise RuntimeError(f"File '{source_file}' not found in coverage.json.")

    uncovered_lines = matched["missing_lines"]
    if not uncovered_lines:
        graph.update(node_id, prompt="No uncovered lines found", response="✅ Fully covered.", status="SKIPPED")
        return node_id

    source_code = Path(source_file).read_text()
    uncovered_str = ", ".join(str(l) for l in uncovered_lines)

    prompt_path = Path(__file__).parent.parent / get_prompt_path("suggest_test_cases.j2")
    template = PromptTemplate.from_template(prompt_path.read_text())
    prompt = template.format(source_code=source_code, uncovered_lines=uncovered_str)

    if debug_prompt:
        print("\n--- Suggest Tests Prompt ---\n" + prompt + "\n--- End Prompt ---\n")

    llm = get_llm_provider()
    suggestions = llm.generate(prompt)

    graph.update(node_id, prompt=prompt, response=suggestions, status="SUGGESTED")
    return node_id