"""RAG: Implementing the RAG flow.

Wraps the flow in a small reusable VectorIndex (add chunks, search by
similarity) and uses it to answer questions with Claude.
"""

import hashlib
import math
import re
from pathlib import Path

from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = Anthropic()
MODEL = "claude-sonnet-5-5"
DIM = 256

DOCUMENT = """# Refunds
Customers may request a refund within 30 days. Refunds go to the original
payment method.

# Shipping
Standard shipping takes 3 to 5 business days. Express shipping takes 1 to 2
business days and costs 15 dollars extra.

# Warranty
Devices include a 2 year limited warranty. Accidental damage is not covered."""


def text_of(message: Message) -> str:
    return "".join(b.text for b in message.content if b.type == "text")


def embed(text: str) -> list[float]:
    """Toy hashed bag-of-words embedding (swap for Voyage AI in real use)."""
    vector = [0.0] * DIM
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        vector[int(hashlib.md5(word.encode()).hexdigest(), 16) % DIM] += 1.0
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


class VectorIndex:
    """In-memory vector store: remembers each chunk with its embedding."""

    def __init__(self) -> None:
        self.texts: list[str] = []
        self.vectors: list[list[float]] = []

    def add(self, text: str) -> None:
        self.texts.append(text)
        self.vectors.append(embed(text))

    def search(self, query: str, k: int = 2) -> list[tuple[float, str]]:
        query_vector = embed(query)
        scored = [
            (cosine(query_vector, vector), text)
            for vector, text in zip(self.vectors, self.texts, strict=True)
        ]
        return sorted(scored, reverse=True)[:k]


def build_index(document: str) -> VectorIndex:
    index = VectorIndex()
    for part in re.split(r"(?m)^(?=# )", document):
        if part.strip():
            index.add(part.strip())
    return index


def answer(index: VectorIndex, question: str) -> str:
    context = "\n\n".join(text for _, text in index.search(question))
    message = client.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": f"<context>\n{context}\n</context>\n\n"
                f"Answer using only the context. If it is missing, say so.\n"
                f"Question: {question}",
            }
        ],
    )
    return text_of(message)


if __name__ == "__main__":
    index = build_index(DOCUMENT)
    for question in ("What does express shipping cost?", "Is water damage covered?"):
        print(f"> {question}\n{answer(index, question)}\n")
