import subprocess

def run_pytest(path="."):
    result = subprocess.run(["pytest", path], capture_output=True, text=True)
    return result.stdout, result.stderr