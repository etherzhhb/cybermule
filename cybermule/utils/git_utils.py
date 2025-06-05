import subprocess
import re


def run_git_command(cmd: list[str], capture_output: bool = False) -> str:
    """Run a Git command and optionally return its output."""
    result = subprocess.run(
        ["git"] + cmd,
        check=True,
        text=True,
        capture_output=capture_output
    )
    return result.stdout.strip() if capture_output else ""


# ─── Branch Operations ─────────────────────────────────────────────────────────

def get_current_branch() -> str:
    """Return the current Git branch name."""
    return run_git_command(["rev-parse", "--abbrev-ref", "HEAD"], capture_output=True)


def checkout_branch(branch: str):
    """Switch to the specified Git branch."""
    run_git_command(["checkout", branch])


def create_new_fix_branch(base: str = "main") -> str:
    """Create and switch to a new fix branch based on the given base branch."""
    branch_id = get_next_fix_branch_id()
    new_branch = f"cybermule/fix-attempt-{branch_id}"
    run_git_command(["checkout", base])
    run_git_command(["pull", "origin", base])
    run_git_command(["checkout", "-b", new_branch])
    return new_branch


def delete_branch(branch: str, base: str = "main"):
    """Delete the specified branch after switching to the base branch."""
    if get_current_branch() == branch:
        run_git_command(["checkout", base])
    run_git_command(["branch", "-D", branch])


def get_next_fix_branch_id() -> int:
    """Determine the next numeric suffix for a fix branch."""
    output = run_git_command(["branch", "--list"], capture_output=True)
    existing = re.findall(r"cybermule/fix-attempt-(\d+)", output)
    existing_ids = sorted(int(x) for x in existing)
    return (existing_ids[-1] + 1) if existing_ids else 1


# ─── Commit Operations ─────────────────────────────────────────────────────────

def run_git_commit(message: str):
    """Stage all changes and commit with the specified message."""
    run_git_command(["add", "."])
    run_git_command(["commit", "-m", message])


def get_latest_commit_sha() -> str:
    """Return the SHA of the latest commit."""
    return run_git_command(["rev-parse", "HEAD"], capture_output=True)


def get_latest_commit_message() -> str:
    """Return the message of the latest commit."""
    return run_git_command(["log", "-1", "--pretty=%B"], capture_output=True)


def get_commit_message_by_sha(sha: str) -> str:
    """Return the commit message for the given SHA."""
    return run_git_command(["log", "-1", "--pretty=%B", sha], capture_output=True)


def get_commit_diff_by_sha(sha: str) -> str:
    """Return the diff for the specified commit SHA."""
    return run_git_command(["show", sha, "--no-color"], capture_output=True)

def get_commits_since(sha: str) -> list[str]:
    """Return a list of commit SHAs made since the given SHA (excluding the SHA itself)."""
    output = run_git_command(["log", f"{sha}..HEAD", "--pretty=%H"], capture_output=True)
    return output.splitlines()

# ─── Repository Introspection ───────────────────────────────────────────────────

def fetch_remote(remote: str = "origin") -> None:
    """Fetch the latest changes from the given remote."""
    run_git_command(["fetch", remote])


def get_last_commit_diff() -> str:
    """Return the diff between HEAD and HEAD~1."""
    return run_git_command(["diff", "HEAD~1", "HEAD"], capture_output=True)
