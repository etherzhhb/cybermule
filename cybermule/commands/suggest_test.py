import typer
from pathlib import Path
from typing import Optional, Tuple, List, Dict

from cybermule.executors.git_review import review_commit_with_llm
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.symbol_resolution import extract_test_definitions


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
    
    
    
    
    typer.echo("✅ Commit review completed")

    # TODO: Generate additional tests based on the commit review and existing tests
    # This would involve:
    # 1. Analyzing the commit changes from review_result
    # 2. Understanding the existing test patterns from test_definitions
    # 3. Using LLM to generate new tests that complement existing ones
    # 4. If not dry_run, write the new tests to appropriate files
    
    if dry_run:
        typer.echo("🧪 Generated tests (dry-run mode):")
        typer.echo("TODO: Use LLM to generate tests based on:")
        typer.echo(f"  - Commit review (node {review_node_id})")
        typer.echo(f"  - {len(test_definitions)} existing test patterns")
    else:
        typer.echo("🧪 Generating additional tests...")
        typer.echo("TODO: Use LLM to generate and apply tests based on:")
        typer.echo(f"  - Commit review (node {review_node_id})")
        typer.echo(f"  - {len(test_definitions)} existing test patterns")
    
    typer.echo("✅ Test suggestion completed")
