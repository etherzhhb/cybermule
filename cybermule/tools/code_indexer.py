import faiss
import numpy as np
import ast
from cybermule.providers.embedding_provider import get_embedding_provider

class CodeIndexer:
    def __init__(self):
        self.embedder = get_embedding_provider()
        self.texts = []
        self.ids = []
        self.index = faiss.IndexFlatL2(self.embedder.output_size)  # MiniLM-L6 output size
        self.next_id = 0

    def add_file(self, path: str):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        chunks = self.extract_code_chunks(content, path)
        for chunk, label in chunks:
            embedding = self.embedder.embed(chunk)
            self.index.add(np.array([embedding], dtype=np.float32))
            self.texts.append(chunk)
            self.ids.append(label)
            self.next_id += 1

    def search(self, query: str, top_k=3):
        embedding = self.embedder.embed(query)
        D, I = self.index.search(np.array([embedding], dtype=np.float32), top_k)
        return [(self.ids[i], self.texts[i]) for i in I[0] if i < len(self.ids)]

    def extract_code_chunks(self, source_code: str, path: str):
        chunks = []
        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    start = node.lineno - 1
                    end = getattr(node, 'end_lineno', start + 1)
                    lines = source_code.splitlines()[start:end]
                    code_chunk = "\n".join(lines)
                    label = f"{path}:{getattr(node, 'name', 'anonymous')}"
                    chunks.append((code_chunk, label))
        except Exception:
            chunks.append((source_code, path))  # fallback to full file
        return chunks