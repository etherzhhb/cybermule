import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.providers.llm_provider import get_llm_provider
from cybermule.utils.config_loader import get_prompt_path
from cybermule.utils.template_utils import render_template

def generate_tests(
    test_samples: List[Dict],
    config: Dict[str, Any],
    graph: Optional[MemoryGraph] = None,
    parent_id: Optional[str] = None):

    local_graph = graph or MemoryGraph()

    node_id = local_graph.new(f"Suggest tests", parent_id=parent_id)


    prompt_path = get_prompt_path(config, name="suggest_test_cases.j2")
    prompt = render_template(prompt_path, {"test_samples": test_samples})

    llm = get_llm_provider(config=config)
    suggestions = llm.generate(prompt)

    local_graph.update(node_id, prompt=prompt, response=suggestions, status="SUGGESTED")
    return suggestions, node_id if graph else None
