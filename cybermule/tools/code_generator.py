from langchain.prompts import PromptTemplate
from pathlib import Path

def load_template(name: str) -> str:
    path = Path(__file__).parent.parent / "prompts" / name
    return path.read_text(encoding="utf-8")

def generate_code(llm, instruction: str, context: str = "") -> str:
    template_str = load_template("generate_code.j2")
    prompt = PromptTemplate.from_template(template_str)
    rendered = prompt.format(task=instruction, context=context)
    return llm.generate(rendered)