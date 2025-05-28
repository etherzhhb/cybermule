## ✅ Cybermule TODO List (All Items)

---

### 🔁 CLI Command Enhancements

#### `generate.py`

1. Allow multiple files to be indexed dynamically.
2. Support configurable output path via `--output` flag.
3. Handle empty or failed generations gracefully (warn or retry).

#### `review_commit.py`

4. Add `--commit <sha>` flag to specify commit.
5. Include file content context from changed files.
6. Support markdown or HTML output formatting for review results.

#### `analyze_coverage.py`

7. Allow custom path to `coverage.json` via CLI flag.
8. Add option to highlight uncovered lines in the source code output.
9. Support batch mode to analyze multiple files in one run.

#### `describe_node.py`

10. Add `--full` flag to show untruncated prompt/response/error fields.
11. Add `--json` flag to return machine-readable output.
12. Use `typer.style` to color-code output based on status or error presence.

#### `filter.py`

13. Add `--print` flag to show the content of matching session logs.
14. Support combined filter feedback (e.g., matching multiple conditions).
15. Add `--directory` option to scan logs in a specified folder.
16. Show summary statistics (e.g., match count, log date range).

#### `history.py`

17. Add `--status` filter to show only nodes with specific status (e.g., FAILED).
18. Support sorting by date, status, or depth.
19. Allow `--json` or `--full` export for machine-readable output.
20. Improve task summary truncation logic (use ellipsis only when needed).

#### `plan.py`

21. Add fallback behavior when LLM output is not valid JSON (e.g., show raw output).
22. Support saving parsed plan steps to a file.
23. Include plan summary in CLI output.
24. Allow specifying a custom prompt template for planning via CLI flag.

#### `planner_loop.py`

25. Add support for manual executor override (skip LLM classification).
26. Add dry-run mode to preview actions without executing.
27. Improve task completion logic: confidence threshold or manual override.
28. Log planner loop run metadata to memory graph.

#### `retry.py`

29. Allow retrying non-code tasks (e.g., planning or review errors).
30. Add `--file` option to control where fixed code is written.
31. Show diff between original and fixed code in CLI.
32. Integrate retry metadata more visibly into the memory graph.

#### `self_correct.py`

33. Add `--dry-run` option to preview steps without running LLM or tests.
34. Log retry summary in the final node.
35. Add visual summary of attempts (tree or indented list).
36. Allow switching executor backends dynamically (e.g., local/test mode).

#### `show_log.py`

37. Add auto-complete support or validation for session log filenames.
38. Add `--key` option to extract and display a specific field (e.g., response).
39. Add color-highlighting or collapsible view for large JSON blocks.
40. Add option to redact or truncate large fields (e.g., prompt/response).

#### `fix_errors.py`

45. Fall back to include error trace in prompt if test node is not found.
46. Allow overriding prompt template path via parameter or config.
47. Optionally return fixed code along with node ID.

#### `run_codegen.py`

48. Add optional context input (e.g., from code index or previous runs).
49. Allow specifying output file name/path.
50. Return generated code in addition to node ID.
51. Support streaming output (if backend allows).

#### `run_tests.py`

52. Allow specifying test path or file pattern.
53. Add support for additional pytest flags.
54. Return stdout and stderr as separate fields in memory graph.
55. Support parsing test result summary (e.g., number passed/failed).

#### `suggest_tests.py`

56. Support batch mode to process multiple source files.
57. Allow fallback behavior when coverage file is missing or malformed.
58. Enable filter for uncovered line count threshold (e.g., skip if < 5).
59. Optionally emit suggestions in markdown or unit test template format.

---

### 🧠 MemoryGraph & Execution Tracking

#### `MemoryGraph` (memory\_graph.py)

60. Add timestamp, mode, and tags metadata to each node.
61. Support rich queries on memory graph (filter by status, depth, etc.).
62. Optionally store raw test logs and LLM token usage stats in nodes.

#### Refactor Plan

63. Move `memory_graph.py` from `tools/` to `memory/` and rename as `context_graph.py` or `memory_graph.py`.
64. Remove `memory/` directory after refactor if no longer needed.

---

### 📦 Prompt Templates

#### `classify_step.j2`

65. Add "Do not explain your choice. Return only the string."

#### `diagnose_failure.j2`

66. Clarify response length (e.g., “Keep explanation under 100 words”).
67. Optionally instruct: “Do not include code”.

#### `fix_code_error.j2`

68. Reinforce: “Do not include explanations or comments.”
69. Optionally add: “If unsure, preserve structure.”

#### `generate_code.j2`

70. Add: “Do not explain or comment the code.”
71. Assume standalone function/script unless otherwise specified.

#### `plan_task.j2`

72. Instruct: “Do not include commentary outside JSON.”
73. Ensure field consistency (`"action"` vs `"description"`).

#### `review_commit.j2`

74. Instruct: “Do not summarize the diff.”
75. Support structured suggestions (bullets/JSON).
76. Add fallback for large diffs.

#### `review_git_commit.j2`

77. Instruct: “Avoid quoting the diff unless necessary.”
78. Optionally format response in structured markdown/JSON.
79. Add fallback for large diffs.

#### `suggest_test_cases.j2`

80. Support markdown or test block formatting.
81. Add flag to return test code only.
82. Add limit/summarization for large input.

---

### 🧠 LLM + Embedding Providers

#### `ClaudeBedrockProvider` (llm\_provider.py)

83. Add support for temperature, top\_p, top\_k tuning.
84. Support streaming output to CLI (if allowed).
85. Log token usage/costs.
86. Define `LLMProvider` interface for multi-backend support.
87. Add error handling (rate limits, formatting).

#### `EmbeddingProvider` (embedding\_provider.py)

88. Add `embed_batch(texts: List[str])`.
89. Add model metadata fields (name, provider).
90. Use `@abc.abstractmethod`.
91. Provide example implementations (OpenAI, Bedrock, SentenceTransformer).

---

### ⚙️ Tools & Utilities

#### `docker_runner.py`

92. Add TODO placeholder or clarify Docker plan.
93. Consider removing if not needed.

#### `code_generator.py`

94. Add debug logging of rendered prompts.
95. Allow overriding template path.
96. Optionally return rendered prompt.

#### `code_indexer.py`

97. Make embedding dimension configurable.
98. Add `embed_batch()` support.
99. Store file path/line numbers.
100. Support indexing docstrings/comments.
101. Return scores or embedding metadata.

#### `compiler.py`

102. Add TODO comment or remove file (currently empty).

#### `config_loader.py`

103. Add config caching.
104. Validate prompt paths.
105. Log warnings for missing/malformed config.

#### `git_inspector.py`

106. Handle edge cases (non-repo, HEAD missing).
107. Support commit SHA diff.
108. Return structured output (file list, hunks).

#### `git_utils.py`

109. Handle `CalledProcessError`.
110. Optionally return stderr.
111. Consider switching to `GitPython`.

---
