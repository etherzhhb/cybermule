[![CI](https://github.com/your-username/cybermule/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/cybermule/actions)

# 🧠 AI Code Agent (CLI)

A command-line AI assistant for coding tasks like:
- Generating Python code from natural language
- Running unit tests and fixing errors automatically
- Reviewing Git commits
- Tracking retry attempts using a memory graph

---

## ✨ Features

| Feature                           | Status |
|-----------------------------------|--------|
| Code generation from task prompts | ✅     |
| Unit test execution and retry loop| ✅     |
| Git commit diff review            | ✅     |
| Memory graph for retries & context| ✅     |
| `--debug-prompt` CLI flag         | ✅     |
| Pluggable prompt templates        | ✅     |
| Configurable backend (Claude via AWS Bedrock) | ✅     |

---

## 🚀 CLI Commands

| `check-llm` | Test connection to the configured LLM provider |
| Command                | Description                                 |
|------------------------|---------------------------------------------|
| `generate`             | Generate code for a given task              |
| `review-commit`        | Analyze latest Git commit                   |
| `history`              | Show memory of past tasks and retries       |
| `describe-node <id>`   | Show full prompt/response for a node        |
| `retry <id>`           | Retry a failed attempt using fix prompt     |

| `analyze-coverage --file X.py` | Suggest tests for uncovered lines in a file     |
| `plan "task desc"`         | Generate a step-by-step plan for a coding task |
| `smart-thread "task" --file X.py` | Full agent workflow: code, test, fix, suggest |
| `planner-loop <plan_id> --file X.py` | Run planned steps (LLM-based executor mapping, auto self-correction, goal check) |
---

## 🧠 Memory Graph

All task runs and retries are saved to `memory_graph.json` with full parent-child linkage.

```txt
Task: Add function
├── Code v1 (fail)
│   └── Retry v2 (pass)
└── Retry v3 (fail)
```

---

## 🛠 Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

OR using `pyproject.toml`:

```bash
pip install .
```

### 2. Configure Bedrock (Claude)

Edit `config.yaml`:

```yaml
llm:
  provider: bedrock
  model_id: anthropic.claude-3-sonnet-20240229-v1:0
  region: us-west-2
```

Make sure AWS credentials are set.

---

## 📂 Project Structure

```
cli/
  main.py                # Typer app entry
  config.yaml            # Config for provider and prompts
commands/
  generate.py            # Main generation command
  review_commit.py       # Git commit review
  retry.py               # Retry a failed node
  history.py             # View past sessions
  describe_node.py       # Show prompt/response for a node
providers/
  llm_provider.py        # Claude via AWS Bedrock
tools/
  memory_graph.py        # Persistent DAG for retries
  test_runner.py         # Runs pytest
  config_loader.py       # Loads config and prompt paths
prompts/
  generate_code.j2       # Prompt for initial code
  fix_code_error.j2      # Prompt for retry after failure
```

---

## ⚙️ Modular Executors

The `executors/` module contains reusable components for running agent steps:

| Executor File         | Purpose                                      |
|-----------------------|----------------------------------------------|
- A step-to-executor classifier (`classify_step.j2`) maps plan steps to the correct executor using LLM reasoning.
| `run_codegen.py`      | Generates code based on task description     |
| `run_tests.py`        | Executes `pytest` and captures test output   |
| `fix_errors.py`       | Uses test feedback to regenerate fixed code  |
| `suggest_tests.py`    | Suggests additional test cases for uncovered lines |

These are used in `smart-thread` and can be composed for more complex agents.

## 🧪 Example

```bash
cybermule plan "Build a CSV parser"
cybermule planner-loop <plan_node_id> --file my_module.py
```
```bash
cybermule smart-thread "Build a CSV parser" --file my_module.py
# Runs codegen → test → fix → suggest-tests
```
```bash
cybermule plan "Build a class that parses JSON"
# Returns a numbered step plan and logs to memory
```
```bash
cybermule analyze-coverage --file my_module.py
# Requires coverage run + coverage json first
```
```bash
cybermule generate
# Generates code and saves result to memory graph

cybermule history
# Lists past tasks and retries

cybermule retry <node_id>
# Retry with updated prompt and test result
```

---

## 📌 Roadmap

- [x] Core generate + retry CLI
- [x] Memory graph for retries
- [ ] GitHub PR integration (deferred)
- [ ] Multi-step planning workflows
- [ ] Test coverage introspection
- [ ] Optional TUI or web UI