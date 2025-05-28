# 🧠 Cybermule Design Overview

Cybermule is a modular AI coding agent designed for autonomous interaction with codebases. It supports code generation, compilation, test execution, error fixing, and Git commit review, all orchestrated through a planner-agent-executor loop.

---

## 📁 Project Structure

```txt
cybermule/
  cli/                  # Typer CLI entrypoint
  commands/             # Subcommand handlers
  providers/            # LLM backends (Claude, OpenAI, etc.)
  tools/                # Test runner, config loader, etc.
  prompts/              # Jinja2 prompt templates
  executors/            # Modular agent execution steps
  memory/               # DAG memory system
tests/                  # Unit and integration tests
README.md
design.md
config.yaml
```

---

## 🧩 Core Components

- **MemoryGraph**: Tracks prompt/response nodes and retry lineage
- **LLM Providers**: Pluggable Claude/OpenAI via Bedrock or API key
- **Executors**: Modular step functions (`run_codegen`, `run_tests`, etc.)
- **Prompt Templates**: Jinja2 templates in `prompts/` used by executors
- **Planner Loop**: Uses `plan.j2` and `classify_step.j2` to map tasks to steps

---

## 🧪 CLI Commands

```bash
cybermule generate             # Generate code from description
cybermule review-commit        # Analyze a Git commit
cybermule retry <node_id>      # Retry failed step with fix
cybermule history              # Show conversation/retry history
cybermule describe-node <id>   # Show full prompt and response
cybermule smart-thread         # Autonomous end-to-end agent thread
cybermule analyze-coverage     # Parse coverage report and suggest tests
cybermule suggest-tests        # Add tests for uncovered functions
cybermule plan                 # Break down task into steps using LLM
cybermule planner-loop         # Execute steps autonomously
cybermule check-llm            # Test LLM connectivity
```

---

## ⚙️ Modular Executors

| File              | Role                                                    |
|-------------------|----------------------------------------------------------|
| `run_codegen.py`  | Generates code from a task prompt                        |
| `run_tests.py`    | Runs unit tests via `pytest`, returns error logs         |
| `fix_errors.py`   | Fixes code based on traceback feedback                   |
| `suggest_tests.py`| Adds new tests for uncovered or critical code paths      |
| `classify_step.j2`| Maps plan steps to executor using LLM reasoning          |

---

## 🔁 Planner + Retry Loop

```txt
[plan.j2] → step → [classify_step.j2] → [executor]
                        ↓
                  [MemoryGraph DAG]
                        ↓
              [retry node] ← [fix_errors.j2]
```

Each step creates a MemoryGraph node with full traceability. Failed steps can be retried or branched.

---

## ✅ Current Status

- Modular CLI via Typer
- Bedrock Claude LLM support
- Prompt templates modularized
- CI test + badge ready
- MemoryGraph DAG implemented
- Executor loop fully functional
- Phase 1–3 complete

---

## 🚧 Coming Up (Phase 4+)

[implementation_plan.md](implementation_plan.md).

