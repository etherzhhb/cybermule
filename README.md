# 🤖 Cybermule – Autonomous AI Agent for Coding

[![CI](https://github.com/etherzhhb/cybermule/actions/workflows/ci.yml/badge.svg)](https://github.com/etherzhhb/cybermule/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/etherzhhb/cybermule/branch/main/graph/badge.svg)](https://codecov.io/gh/etherzhhb/cybermule)

**Cybermule** is an autonomous AI-powered CLI agent that detects test failures, analyzes them using LLMs (Claude, OpenAI), and automatically proposes, applies, verifies, and tracks code fixes — safely and iteratively, using Git.

🔧 Designed to fix failing tests, review commits, and track retry attempts in a memory graph. Modular, pluggable, and optimized for LLM-assisted debugging.

---

## 🧩 Core Features

| Feature                                      | Status |
|---------------------------------------------|--------|
| Pytest failure detection and trace parsing  | ✅     |
| Multi-round LLM fix reasoning (`CoT`)       | ✅     |
| Structured fix plan w/ Aider-style patches  | ✅     |
| Git branch isolation and rollback           | ✅     |
| MemoryGraph to track attempts and context   | ✅     |
| Symbol resolution for context requests      | ✅     |
| CLI tools for automation                    | ✅     |
| Claude/OpenAI/AWS Bedrock support           | ✅     |

---

## 🚀 Getting Started

### 🛠️ Install

Install required dependencies:

```bash
# Install system dependencies
brew install --HEAD universal-ctags/universal-ctags/universal-ctags  # macOS
sudo apt install universal-ctags  # Ubuntu

# Install Aider
pip install aider-install
aider-install

# Clone and install Cybermule
git clone https://github.com/etherzhhb/cybermule.git
cd cybermule
pip install -e .
```

---

## ⚙️ Configuration (`config.yaml`)

Here's a sample configuration for Cybermule using LiteLLM:

```yaml
litellm:
  model: "claude-3-5-haiku-20241022"
  max_tokens: 8192
  debug_prompt: true

setup_command: |
  pip install -e .

test_command: |
  pytest --tb=short -q

single_test_command: |
  pytest -q -k {test_name} --tb=short
```

---

## 🧠 How It Works

Cybermule automates the test-debug-fix cycle using this loop:

1. **Run Pytest** → detect failing tests
2. **Extract First Failure** → parse traceback
3. **LLM Summary** → explain failure in natural language
4. **Fix Plan Generation** → propose JSON fix plan
5. **Code Edit (via Aider)** → patch the code with Git safety
6. **Rerun Test** → validate fix or retry with new branch
7. **Track in Memory Graph** → store attempt + reasoning trace

---

## 🗂️ Project Structure

```text
cybermule/
├── commands/            # CLI entrypoints (e.g., run-and-fix)
├── executors/           # LLM logic: traceback analysis, fix generation
├── tools/               # Git and test runners
├── utils/               # Symbol resolution, AST tools
├── memory/              # Memory graph and commit history
├── prompts/             # Prompt templates (Jinja2)
├── symbol_resolution/   # Ctags + AST + semantic search
```

---

## 📦 CLI Usage

```bash
# Run the full fix loop
cybermule run-and-fix

# Review last commit
cybermule review-commit
```

Supports filtering by test name, file, or error.

---

## 📘 Prompt Format

### Fix Plan Example

```json
{
  "fix_description": "Fix condition in test case",
  "symbol": "TestExample.test_something",
  "edits": [
    {
      "file": "tests/test_example.py",
      "line": 42,
      "code_snippet": "assert x == 1"
    }
  ]
}
```

---

## 🧠 Memory Graph

All reasoning steps (traceback → summary → fix plan) are stored in a DAG using `MemoryGraph`, enabling future review, debugging, or replay.

Also used for:
- Retry tracking
- Fix lineage
- Commit review prompts

---

## 🧩 Context Extraction

When the LLM says it needs more code context:

```json
{
  "needs_more_context": true,
  "request_description": "...",
  "required_info": [
    {
      "symbol": "extract_locations",
      "ref_path": "utils/context_extract.py",
      "ref_function": "get_context_snippets"
    }
  ]
}
```

Cybermule extracts relevant snippets using:
- AST (preferred)
- Ctags
- Tree-sitter fallback
- Optional semantic search (e.g. FAISS)

---

## 🔌 Supported LLMs

- Claude via AWS Bedrock
- OpenAI (GPT-4)
- Ollama (local inference)

---

## ✅ Tests

```bash
pytest tests/
```

Includes tests for:
- CLI
- Fix generation
- Symbol resolution
- Git safety
- Context enrichment

---

## 📚 Related Files

- [`design.md`](design.md) – System architecture
- [`implementation_plan.md`](implementation_plan.md) – Development roadmap

---

## 🛡️ Philosophy

- 🔒 **Safe by Default** – Git branches, commits, undo support
- 🔁 **Fix, Test, Retry** – Multi-round AI reasoning
- 🧠 **Context-Aware** – Extracts only what the LLM needs
- 💬 **Transparent** – All decisions logged and reviewable

---

## 📬 Feedback

Pull requests and issues welcome!
