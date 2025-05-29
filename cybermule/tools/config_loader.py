import os
import yaml
from pathlib import Path

def load_config():
    default_path  = Path(__file__).parent.parent / "config.yaml"
    config_path = os.environ.get("CYBER_MULE_CONFIG")
   
    path = Path(config_path) if config_path else default_path
   
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_prompt_path(name: str) -> str:
    config = load_config()
    return config.get("prompt_paths", {}).get(name, f"prompts/{name}.j2")
