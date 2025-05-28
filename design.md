# 🧠 AI Code Agent – Progress Summary

## ✅ Phase 1: CLI Agent Core
- Modular CLI via **Typer**
- Configurable prompts using **Jinja2**
- Claude via **AWS Bedrock**
- Git integration: commit diff + message
- `generate`, `review-commit` commands
- Prompt debugging: `--debug-prompt`
- JSON memory log for each run

## 🧠 Phase 2: Memory + Retry Graph
- Persistent **MemoryGraph** stores prompt/response DAG
- `history`, `describe-node`, `retry <node_id>` commands
- Node lineage tracking for retries/fixes

## 📂 Phase 3: Code Review + Coverage
- `review-commit`: code reviewer using Git diff + Claude
- `analyze-coverage`: suggest tests from coverage JSON
- `suggest_tests.py` module added
- Executor-based modular pipeline

## 🔄 Phase 4: Smart Thread (Agent Loop)
- `smart-thread`: one-shot task handler (generate → test → fix)
- `plan`: multi-step planner using LLM (`plan_task.j2`)
- Modular `executors/`:
  - `run_codegen.py`
  - `run_tests.py`
  - `fix_errors.py`
  - `suggest_tests.py`

## 🧭 Phase 5: Planner Loop System
- `planner-loop <plan_id>` executes plan steps in order
- Steps are parsed from LLM JSON output
- Executor dispatch is now **LLM-based** via `classify_step.j2`
- Goal completion is checked via `task_done.j2`
- Final result: **agent can plan, execute, adapt, and decide when done**

## 🧪 CLI Commands

| Command                       | Description                                           |
|-------------------------------|-------------------------------------------------------|
| `generate`                    | Generate code from prompt                            |
| `review-commit`               | Review a Git commit with Claude                      |
| `retry <node_id>`             | Retry or fix a failed node                           |
| `plan`                        | Break down a task into executable steps              |
| `planner-loop <plan_id>`      | Execute steps, LLM-mapped executors, check goal      |
| `smart-thread --file X.py`    | Run code → test → fix → suggest in one go            |
| `analyze-coverage --file`     | Suggest missing tests from coverage.json             |
| `history`, `describe-node`    | View memory graph nodes                              |

## 🧠 Prompts Used

- `generate_code.j2`
- `review_git_commit.j2`
- `plan_task.j2`
- `classify_step.j2`
- `task_done.j2`
- `fix_code_error.j2`
- `suggest_test_cases.j2`

## ✅ Status Summary

| Feature                        | Status  |
|--------------------------------|---------|
| Modular CLI                    | ✅ Done  |
| Bedrock Claude integration     | ✅ Done  |
| Git diff + review              | ✅ Done  |
| MemoryGraph                    | ✅ Done  |
| Retry/fix loop                 | ✅ Done  |
| Codegen + test executor        | ✅ Done  |
| Planner + classifier loop      | ✅ Done  |
| Task completion detection      | ✅ Done  |
| UI (TUI or web)                | ⏸️ On hold |
| GitHub PR integration          | ⏸️ On hold |
| PyPI / packaging               | 🔜 Next  |

## 🔄 Phase 6: Self-Correction Workflow

- `diagnose_failure.j2` prompt to explain test/code failure
- `self-correct <node_id> --file X.py` command:
  - Diagnose → Fix → Re-test (retry loop)
  - Uses `fix_code_error.j2` + `run_tests.py`
- Integrated into `planner-loop`: auto self-correct after failed test
- Supports retry budget (`max_retries`)
- Fully documented in `README.md`

## 📦 Phase 7: Packaging and CLI Distribution

- 🔁 Renamed project to **CyberMule**
- 🧩 Package structure reorganized under `cybermule/`
- ✅ Added `setup.py` and `pyproject.toml`
- ✅ Exposed CLI via entry point: `cybermule=cybermule.cli.main:app`
- 📄 Added `__init__.py` with versioning
- 🧪 Project can now be installed with `pip install .`
- 📘 CLI command is available as: `cybermule <subcommand>`