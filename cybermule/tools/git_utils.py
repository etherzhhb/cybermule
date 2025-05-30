import subprocess

def run_git_command(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()

def get_latest_commit_sha() -> str:
    return run_git_command(["git", "rev-parse", "HEAD"])

def get_latest_commit_message() -> str:
    return run_git_command(["git", "log", "-1", "--pretty=%B"])

def get_latest_commit_diff() -> str:
    return run_git_command(["git", "diff", "HEAD~1", "HEAD"])

def fetch_remote(remote: str) -> None:
    """Fetch latest changes from the given remote."""
    run_git_command(["git", "fetch", remote])

def get_commit_message(sha: str) -> str:
    """Get commit message for a specific SHA."""
    return run_git_command(["git", "log", "-1", "--pretty=%B", sha])

def get_commit_diff(sha: str) -> str:
    """Get diff for a specific commit SHA."""
    return run_git_command(["git", "show", sha, "--no-color"])
