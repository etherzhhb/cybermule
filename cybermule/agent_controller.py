import argparse
import json
import os
from datetime import datetime
from cybermule.providers.llm_provider import ClaudeBedrockProvider
from tools import code_generator, test_runner, code_indexer, git_inspector

def log_session(data, mode):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"session_{mode}_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Session logged to {filename}")

def list_session_logs():
    logs = [f for f in os.listdir("..") if f.startswith("session_") and f.endswith(".json")]
    if not logs:
        print("No session logs found.")
    else:
        print("Session logs:")
        for log in sorted(logs):
            print("  ", log)

def show_session_log(filename):
    if not os.path.exists(filename):
        print(f"Log file not found: {filename}")
        return
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
        print(json.dumps(data, indent=2))

def filter_session_logs(keyword=None, mode=None, date=None):
    logs = [f for f in os.listdir("..") if f.startswith("session_") and f.endswith(".json")]
    found = False
    for log in sorted(logs):
        try:
            with open(log, "r", encoding="utf-8") as f:
                data = json.load(f)
                content = json.dumps(data).lower()

                if keyword and keyword.lower() not in content:
                    continue
                if mode and data.get("mode") != mode:
                    continue
                if date:
                    timestamp = data.get("timestamp", "")
                    if not timestamp.startswith(date):
                        continue

                print(f"Match in: {log}")
                found = True
        except Exception:
            continue
    if not found:
        print("No logs matched the given filters.")

def generate_mode(claude):
    session_log = {"mode": "generate", "timestamp": datetime.now().isoformat()}
    task = input("What do you want the agent to do?\n> ")
    session_log["task"] = task

    indexer = code_indexer.CodeIndexer()
    for fname in ["generated_code.py"]:
        try:
            indexer.add_file(fname)
        except FileNotFoundError:
            pass

    context_snippets = indexer.search(task)
    combined_context = "\n\n".join([code for _, code in context_snippets])
    session_log["retrieved_context"] = combined_context

    code = code_generator.generate_code(claude, task, combined_context)
    session_log["initial_code"] = code

    with open("generated_code.py", "w", encoding="utf-8") as f:
        f.write(code)

    stdout, stderr = test_runner.run_pytest()
    session_log["initial_test_output"] = stdout
    session_log["initial_test_errors"] = stderr

    if "FAILED" in stdout or "error:" in stderr:
        fix_prompt = f"The following code had errors:\n{code}\n\nError Output:\n{stderr}\n\nPlease fix the code."
        fixed_code = claude.generate(fix_prompt)
        session_log["fixed_code"] = fixed_code

        with open("generated_code.py", "w", encoding="utf-8") as f:
            f.write(fixed_code)

        stdout, stderr = test_runner.run_pytest()
        session_log["final_test_output"] = stdout
        session_log["final_test_errors"] = stderr

    log_session(session_log, "generate")

def review_commit_mode(claude):
    session_log = {"mode": "review-commit", "timestamp": datetime.now().isoformat()}

    git = git_inspector.GitInspector()
    commit_msg = git.get_commit_message()
    diff = git.get_last_commit_diff()

    session_log["commit_message"] = commit_msg
    session_log["commit_diff"] = diff

    context = f"Commit Message:\n{commit_msg}\n\nDiff:\n{diff}"
    review = claude.generate(f"Review the following commit and provide feedback or suggestions:\n{context}")
    session_log["commit_review"] = review

    print("Commit Review:\n", review)
    log_session(session_log, "review_commit")

def main():
    parser = argparse.ArgumentParser(description="AI Coding Agent")
    parser.add_argument("--mode", choices=["generate", "review-commit"], help="Run mode")
    parser.add_argument("--history", action="store_true", help="List past session logs")
    parser.add_argument("--show-log", type=str, help="Show the contents of a session log")
    parser.add_argument("--filter", type=str, help="Search logs for a keyword")
    parser.add_argument("--filter-mode", choices=["generate", "review-commit"], help="Filter logs by mode")
    parser.add_argument("--filter-date", type=str, help="Filter logs by date (YYYY-MM-DD)")
    args = parser.parse_args()

    if args.history:
        list_session_logs()
        return

    if args.show_log:
        show_session_log(args.show_log)
        return

    if args.filter or args.filter_mode or args.filter_date:
        filter_session_logs(keyword=args.filter, mode=args.filter_mode, date=args.filter_date)
        return

    claude = ClaudeBedrockProvider()

    if args.mode == "generate":
        generate_mode(claude)
    elif args.mode == "review-commit":
        review_commit_mode(claude)
    else:
        print("Please provide a valid --mode or use --history, --show-log, or filters.")

if __name__ == "__main__":
    main()