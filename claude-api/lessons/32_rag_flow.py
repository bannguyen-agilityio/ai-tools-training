"""RAG: The full RAG flow.

Two phases:

  Ingest (once):  document -> chunks -> embeddings -> vector store
  Query (always): question -> embedding -> top-k similar chunks -> prompt -> Claude

This script walks through every step and prints the intermediate result, ending
with the augmented prompt (no API call; the next lesson sends it).
"""

import hashlib
import math
import re

DOCUMENT = """# Refunds
Customers may request a refund within 30 days. Refunds go to the original
payment method.

# Shipping
Standard shipping takes 3 to 5 business days. Express shipping takes 1 to 2
business days and costs 15 dollars extra.

# Warranty
Devices include a 2 year limited warranty. Accidental damage is not covered."""

DIM = 256


def embed(text: str) -> list[float]:
    """Toy hashed bag-of-words embedding (swap for Voyage AI in real use)."""
    vector = [0.0] * DIM
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        vector[int(hashlib.md5(word.encode()).hexdigest(), 16) % DIM] += 1.0
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def chunk_by_section(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"(?m)^(?=# )", text) if p.strip()]


if __name__ == "__main__":
    # 1-3. Ingest: chunk, embed, store (a list of pairs is our "vector store").
    chunks = chunk_by_section(DOCUMENT)
    store: list[tuple[list[float], str]] = [(embed(c), c) for c in chunks]
    print(f"[ingest] {len(chunks)} chunks stored")

    # 4. Embed the user's question with the SAME model as the chunks.
    question = "What does express shipping cost?"
    query_vector = embed(question)

    # 5. Retrieve the top-k most similar chunks.
    top_k = 2
    ranked = sorted(store, key=lambda item: cosine(query_vector, item[0]), reverse=True)
    retrieved = [chunk for _, chunk in ranked[:top_k]]
    print(f"[retrieve] top {top_k}: {[c.splitlines()[0] for c in retrieved]}")

    # 6. Augment: put the retrieved chunks in the prompt.
    context = "\n\n".join(retrieved)
    prompt = f"<context>\n{context}\n</context>\n\nQuestion: {question}"
    print(f"[prompt]\n{prompt}")
