import pytest
from cybermule.utils.parsing import (
    extract_tagged_blocks,
    extract_code_blocks,
    extract_first_json_block,
)


def test_extract_json_block_valid():
    text = """```json
{
  "file": "src/example.py",
  "line": 10,
  "fix_description": "Fix off-by-one error",
  "code_snippet": "return x + 1"
}
```"""
    result = extract_first_json_block(text)
    assert isinstance(result, dict)
    assert result["file"] == "src/example.py"
    assert result["line"] == 10


def test_extract_json_block_invalid():
    text = """```json
{ invalid json
```"""
    result = extract_first_json_block(text)
    assert result is None


def test_extract_json_block_no_json():
    text = "This is just a string without code blocks"
    result = extract_first_json_block(text)
    assert result is None


def test_extract_single_block():
    text = """Some text before.
    <error_summary>
    Exception Type: ValueError
    Details: invalid input
    </error_summary>
    Some text after."""
    result = extract_tagged_blocks(text, "error_summary")
    assert len(result) == 1
    assert "ValueError" in result[0]


def test_extract_multiple_blocks():
    text = """<error_summary>First block</error_summary>
    Noise
    <error_summary>Second block</error_summary>"""
    result = extract_tagged_blocks(text, "error_summary")
    assert len(result) == 2
    assert "First block" in result[0]
    assert "Second block" in result[1]


def test_detect_nested_block_error():
    text = """<error_summary>
    Outer block
    <error_summary>Nested block</error_summary>
    </error_summary>"""
    with pytest.raises(
        ValueError, match="Nested <error_summary> blocks are not allowed."
    ):
        extract_tagged_blocks(text, "error_summary")

def test_extract_custom_tag():
    text = """<debug_info>Debug details here</debug_info>"""
    result = extract_tagged_blocks(text, "debug_info")
    assert len(result) == 1
    assert "Debug details here" in result[0]


def test_extract_single_python_block():
    text = """```python
def foo(): return 42
```"""
    blocks = extract_code_blocks(text)
    assert len(blocks) == 1
    assert "def foo()" in blocks[0]


def test_extract_multiple_python_blocks():
    text = """```python
def foo(): pass
```

Noise

```python
def bar(): pass
```"""
    blocks = extract_code_blocks(text)
    assert len(blocks) == 2
    assert "foo" in blocks[0]
    assert "bar" in blocks[1]


def test_extract_python_block_with_blank_info():
    text = """```
# no language specified
def fallback(): pass
```"""
    blocks = extract_code_blocks(text)
    assert len(blocks) == 1
    assert "fallback" in blocks[0]


def test_extract_ignores_non_python_blocks():
    text = """```json
{ "key": "value" }
```

```js
function test() {}
```"""
    blocks = extract_code_blocks(text)
    assert blocks == []
