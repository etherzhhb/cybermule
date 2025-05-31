from pathlib import Path
import jinja2

def render_template(template_path: Path, template_vars: dict) -> str:
    """
    Load and render a Jinja2 template with the provided variables.

    Args:
        template_path: Path to the template file
        template_vars: Dictionary of variables to render in the template

    Returns:
        Rendered template as a string
    """
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_path.parent),
        autoescape=jinja2.select_autoescape()
    )
    template = env.get_template(template_path.name)
    return template.render(**template_vars)
