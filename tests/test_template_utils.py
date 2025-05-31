import pytest
from pathlib import Path
from cybermule.utils.template_utils import render_template

def test_render_valid_template(tmp_path):
    template_path = tmp_path / "greet.j2"
    template_path.write_text("Hello, {{ name }}!")
    result = render_template(template_path, {"name": "CyberMule"})
    assert result == "Hello, CyberMule!"

def test_render_template_missing_variable(tmp_path):
    template_path = tmp_path / "incomplete.j2"
    template_path.write_text("Age: {{ age }}")
    result = render_template(template_path, {})
    assert "Age:" in result  # Jinja2 renders missing variables as empty strings
    assert result.strip() == "Age:"

def test_render_template_with_syntax_error(tmp_path):
    template_path = tmp_path / "bad.j2"
    template_path.write_text("Hello {% if name %}")  # malformed template
    with pytest.raises(Exception):
        render_template(template_path, {"name": "CyberMule"})
