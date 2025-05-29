import pytest
import yaml
from unittest.mock import patch

# Autouse fixture to patch load_config() across all tests
def load_test_config():
    with open("config.test.yaml") as f:
        return yaml.safe_load(f)

def pytest_sessionstart(session):
    patcher = patch("cybermule.tools.config_loader.load_config", side_effect=load_test_config)
    patcher.start()
    session._cybermule_config_patcher = patcher

def pytest_sessionfinish(session, exitstatus):
    if hasattr(session, "_cybermule_config_patcher"):
        session._cybermule_config_patcher.stop()
