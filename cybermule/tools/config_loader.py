import os
import yaml
from pathlib import Path

def load_config():
    path = Path(os.environ.get("CYBER_MULE_CONFIG", "config.yaml"))
   
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_prompt_path(name: str) -> str:
    config = load_config()
    return config.get("prompt_paths", {}).get(name, f"prompts/{name}")
