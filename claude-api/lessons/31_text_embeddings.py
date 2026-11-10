"""RAG: Text embeddings.

An embedding turns text into a list of numbers so that similar meanings are
close together. Closeness is measured with cosine similarity (1 = same
direction, 0 = unrelated).

Anthropic has no embeddings endpoint; the course uses Voyage AI. To stay
dependency-free this script uses a toy hashed bag-of-words embedding, which only
captures shared *words*, not real meaning. Swap `embed` for a Voyage call
(`voyageai.Client().embed(texts, model=...)`) and nothing else changes.
"""

import hashlib
import math
import re

DIM = 256


def embed(text: str) -> list[float]:
    """Toy embedding: hash each word into a bucket, then L2-normalise."""
    vector = [0.0] * DIM
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        bucket = int(hashlib.md5(word.encode()).hexdigest(), 16) % DIM
        vector[bucket] += 1.0
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    # Vectors are already unit length, so the dot product is the cosine.
    return sum(x * y for x, y in zip(a, b, strict=True))


if __name__ == "__main__":
    query = "how long does express shipping take"
    texts = [
        "Express shipping takes 1 to 2 business days.",
        "Refunds are returned to the original payment method.",
        "The warranty covers manufacturing defects for 2 years.",
    ]
    query_vector = embed(query)
    print(f"dimensions: {len(query_vector)}")
    ranked = sorted(
        ((cosine_similarity(query_vector, embed(t)), t) for t in texts), reverse=True
    )
    for score, text in ranked:
        print(f"{score:.3f}  {text}")
