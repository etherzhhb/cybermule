from pathlib import Path
import jinja2
from jinja2 import meta

def render_template(template_path: Path, template_vars: dict) -> str:
    """
    Load and render a Jinja2 template with the provided variables.

    This function enforces that all variables passed in `template_vars` are 
    actually used in the template. It will raise a ValueError if any key in 
    `template_vars` is not referenced in the template body.

    ⚠️ It is the caller's responsibility to ensure that `template_vars` does not 
    contain any unused keys. This strict check helps avoid configuration drift, 
    dead parameters, or mismatches between input and template structure.

    Args:
        template_path: Path to the Jinja2 template file.
        template_vars: Dictionary of variables to be used in rendering. 
                       All keys must be used in the template.

    Returns:
        Rendered template as a string.

    Raises:
        ValueError: If any key in `template_vars` is not used in the template.
    """
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_path.parent),
        autoescape=jinja2.select_autoescape()
    )

    # Parse template source to find used variables
    source = env.loader.get_source(env, template_path.name)[0]
    parsed_content = env.parse(source)
    used_vars = meta.find_undeclared_variables(parsed_content)

    # Check for unused variables
    unused_keys = set(template_vars.keys()) - used_vars
    if unused_keys:
        raise ValueError(f"Unused variables in context: {unused_keys}")

    template = env.get_template(template_path.name)
    return template.render(**template_vars)
