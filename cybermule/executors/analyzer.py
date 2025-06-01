from pathlib import Path
from typing import Any, Dict, Tuple, Optional
import json

from markdown_it import MarkdownIt

from cybermule.providers.llm_provider import get_llm_provider
from cybermule.tools.config_loader import get_prompt_path
from cybermule.utils.template_utils import render_template


def extract_json_block(text: str) -> Optional[dict]:
    """
    Extract and parse the first ```json fenced block from the text.

    Args:
        text: Raw LLM output (may contain Markdown or prose)

    Returns:
        A parsed dictionary if found and valid, otherwise None
    """
    md = MarkdownIt()
    tokens = md.parse(text)

    for t in tokens:
        if t.type == "fence" and t.info.strip() == "json":
            try:
                return json.loads(t.content)
            except json.JSONDecodeError:
                return None

    return None


def analyze_failure_with_llm(
    traceback: str,
    config: Dict[str, Any],
    history: Tuple[Dict[str, Any], ...] = (),
) -> dict:
    """
    Analyze a pytest failure using stepwise Chain-of-Thought reasoning via an LLM.

    Args:
        traceback: The raw traceback string from a failed pytest test.
        config: Project config to load prompt and select LLM provider.
        history: Optional conversation history for multi-turn refinement.

    Returns:
        A dictionary with keys like 'file', 'line', 'fix_description', 'code_snippet'.
    """
    try:
        llm = get_llm_provider(config)

        prompt_path = get_prompt_path(config, "fix_traceback.j2")
        template_path = Path(prompt_path)
        prompt = render_template(template_path, {"traceback": traceback})

        result_text = llm.generate(prompt, history=history)

        # Attempt structured parse first
        parsed = extract_json_block(result_text)
        if parsed:
            return parsed

        # Fallback: raw JSON decode (in case no fenced block used)
        return json.loads(result_text)

    except Exception as e:
        print(f"[analyze_failure_with_llm] Error: {e}")
        return {}


def summarize_traceback(
    traceback: str,
    config: Dict[str, Any],
    history: Tuple[Dict[str, Any], ...] = (),
) -> str:
    """
    Use an LLM to summarize what happened in the traceback and explain the error.

    Args:
        traceback: The full traceback string from a failed test.
        config: Project configuration, used to locate the summary prompt and LLM.
        history: Optional message history for multi-turn reasoning.

    Returns:
        A human-readable summary string from the LLM.
    """
    try:
        llm = get_llm_provider(config)
        prompt_path = get_prompt_path(config, "summarize_traceback.j2")
        template_path = Path(prompt_path)
        prompt = render_template(template_path, {"traceback": traceback})
        return llm.generate(prompt, history=history)

    except Exception as e:
        print(f"[summarize_traceback] Error: {e}")
        return "Failed to summarize traceback."
