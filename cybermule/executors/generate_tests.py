import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.executors.llm_runner import llm_run

def generate_tests(
    test_samples: List[Dict], hints: str,
    config: Dict[str, Any],
    graph: Optional[MemoryGraph] = None,
    parent_id: Optional[str] = None):

    files = set(test['file'] for test in test_samples)
    all_existing_tests = "\n\n".join(Path(file).read_text() for file in files)

    suggestions, node_id = llm_run(
        config=config,
        graph=graph,
        title=f"Suggest tests",
        parent_id=parent_id, 
        tags=["suggestion"],
        prompt_template="suggest_test_cases.j2",
        variables={
            "test_samples": test_samples,
            "all_existing_tests": all_existing_tests,
            "hints": hints
        },
        status="SUGGESTED"
    )

    return suggestions, node_id
