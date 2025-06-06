import typer
from pathlib import Path
from typing import Optional, Tuple, List, Dict

from cybermule.executors.apply_code_change import apply_code_change
from cybermule.executors.generate_tests import generate_tests
from cybermule.executors.git_review import review_commit_with_llm
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.symbol_resolution import extract_test_definitions
from cybermule.utils.config_loader import get_prompt_path
from cybermule.utils.parsing import extract_code_blocks
from cybermule.utils.template_utils import render_template


def parse_pytest_path(test_spec: str) -> Tuple[Path, Optional[str]]:
    """
    Parse pytest notation like 'path/to/test.py::test_function' or 'path/to/test.py::Class::test_method'
    
    Returns:
        (file_path, test_identifier) where test_identifier is None if no :: found
    """
    if "::" in test_spec:
        file_part, test_part = test_spec.split("::", 1)
        return Path(file_part), test_part
    else:
        return Path(test_spec), None


def run(
    ctx: typer.Context,
    test_path: str = typer.Argument(
        ...,
        help="Path to existing test file or specific test using pytest notation (e.g., path/test.py::test_function)",
    ),
    hints: str = typer.Option("", help="Refactoring goal, e.g., 'extract class', 'rename variable'"),
    review_commit: bool = typer.Option(False, help="Run a commit review before analyzing test failure."),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Only show new tests without applying them",
    ),
):
    """Suggest additional tests based on existing test file and commit review."""
    config = ctx.obj["config"]

    # Parse the test path to handle pytest notation
    file_path, test_identifier = parse_pytest_path(test_path)

    # Validate that the file exists
    if not file_path.exists():
        typer.echo(f"❌ Test file does not exist: {file_path}", err=True)
        raise typer.Exit(1)

    if not file_path.is_file():
        typer.echo(f"❌ Path is not a file: {file_path}", err=True)
        raise typer.Exit(1)

    # Initialize memory graph
    graph = MemoryGraph()

    # First, review the commit
    typer.echo("🔍 Reviewing commit...")

    review_node_id = None
    if review_commit:
        typer.echo("[run_and_fix] Reviewing latest commit...")
        review, review_node_id = review_commit_with_llm(config, graph=graph)
        typer.echo(review)
        typer.echo("✅ Commit review completed")

    # Extract test function definitions
    typer.echo("📋 Extracting test definitions...")
    test_definitions = extract_test_definitions(file_path, test_identifier)

    if not test_definitions:
        typer.echo(f"❌ No test definitions found in {file_path}", err=True)
        if test_identifier:
            typer.echo(f"   Specifically looking for: {test_identifier}")
        raise typer.Exit(1)

    # Log what we extracted
    typer.echo(f"📋 Using test file: {file_path}")
    if test_identifier:
        typer.echo(f"🎯 Extracted specific test: {test_identifier}")
    else:
        typer.echo(f"🎯 Extracted {len(test_definitions)} test functions")

    # Display extracted test information
    for i, test_def in enumerate(test_definitions, 1):
        typer.echo(f"  {i}. {test_def['symbol']} (line {test_def['start_line']})")
        if dry_run:
            typer.echo(f"     Preview: {test_def['snippet'][:100]}...")

    typer.echo("🧪 Generating additional tests...")

    tests, suggest_test_id = generate_tests(
      test_samples=test_definitions, hints=hints, config=config, graph=graph,
      parent_id=review_node_id)

    tests_code = '\n\n'.join(extract_code_blocks(tests))

    typer.echo(f"Suggested tests:\n{tests_code}")

    if  dry_run:
        typer.echo("🎯 Dry run, not applying tests")
        return


    prompt_path = get_prompt_path(config, "aider_integrate_test.j2")
    message = render_template(Path(prompt_path),
                             template_vars={"FILE": file_path,
                                            "TEST_CODE": tests_code})

    apply_code_change(description="Add extra test",
                      file_paths=[str(file_path)], message=message,
                      config=config, graph=graph, parent_id=suggest_test_id,
                      operation_type="add test")

    typer.echo("✅ Test suggestion completed")
