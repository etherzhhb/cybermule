from pathlib import Path


def get_prompt_path(config, name: str) -> str:
    return config.get("prompt_paths", {}).get(name, Path(__file__).parent.parent / f"prompts/{name}")

def get_aider_extra_args(config: dict) -> list[str]:
    """
    Converts the LLM config section into Aider CLI args.
    Supports model, API key, and optional overrides under aider.extra_args.
    """
    args = []

    llm_cfg = config.get("litellm", {})
    aider_cfg = config.get("aider", {})

    if model := llm_cfg.get("model"):
        args += ["--model", model]
    if api_key := llm_cfg.get("api_key"):
        args += ["--api-key", api_key]

    # Optional overrides
    if isinstance(aider_cfg.get("extra_args"), list):
        args += aider_cfg["extra_args"]

    return args
