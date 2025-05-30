import os
import yaml
from pathlib import Path


def get_prompt_path(config, name: str) -> str:
    return config.get("prompt_paths", {}).get(name, f"prompts/{name}")
