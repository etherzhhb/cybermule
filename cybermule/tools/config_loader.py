import yaml
from pathlib import Path

def load_config():
    path = Path(__file__).parent.parent / "config.yaml"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

def get_prompt_path(name: str) -> str:
    config = load_config()
    return config.get("prompt_paths", {}).get(name, f"prompts/{name}.j2")