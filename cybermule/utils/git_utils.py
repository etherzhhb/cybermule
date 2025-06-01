import subprocess
import re


def run_git_command(cmd: list[str], capture_output: bool = False) -> str:
    """Run a git command and optionally capture output."""
    result = subprocess.run(
        ["git"] + cmd,
        check=True,
        text=True,
        capture_output=capture_output
    )
    return result.stdout.strip() if capture_output else ""


def get_current_branch() -> str:
    """Return the name of the current Git branch."""
    return run_git_command(["rev-parse", "--abbrev-ref", "HEAD"], capture_output=True)


def checkout_branch(branch: str):
    """Switch to the given Git branch."""
    run_git_command(["checkout", branch])


def create_new_fix_branch(base: str = "main") -> str:
    """Create a new fix branch from the given base branch."""
    branch_id = get_next_fix_branch_id()
    new_branch = f"cybermule/fix-attempt-{branch_id}"
    run_git_command(["checkout", base])
    run_git_command(["pull", "origin", base])
    run_git_command(["checkout", "-b", new_branch])
    return new_branch


def delete_branch(branch: str, base: str = "main"):
    """Delete the specified branch after switching back to base."""
    if get_current_branch() == branch:
        run_git_command(["checkout", base])
    run_git_command(["branch", "-D", branch])


def run_git_commit(message: str):
    """Stage all changes and commit with the given message."""
    run_git_command(["add", "."])
    run_git_command(["commit", "-m", message])

def get_next_fix_branch_id() -> int:
    """Return the next available fix branch ID."""
    output = run_git_command(["branch", "--list"], capture_output=True)
    existing = re.findall(r"cybermule/fix-attempt-(\d+)", output)
    existing_ids = sorted(int(x) for x in existing)
    return (existing_ids[-1] + 1) if existing_ids else 1

def get_latest_commit_sha() -> str:
    return run_git_command(["git", "rev-parse", "HEAD"])

def get_latest_commit_message() -> str:
    return run_git_command(["git", "log", "-1", "--pretty=%B"])

def fetch_remote(remote: str) -> None:
    """Fetch latest changes from the given remote."""
    run_git_command(["git", "fetch", remote])

def get_commit_message(sha: str) -> str:
    """Get commit message for a specific SHA."""
    return run_git_command(["git", "log", "-1", "--pretty=%B", sha])

def get_commit_diff(sha: str) -> str:
    """Get diff for a specific commit SHA."""
    return run_git_command(["git", "show", sha, "--no-color"])
