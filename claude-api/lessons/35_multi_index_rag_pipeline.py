"""RAG: A multi-index RAG pipeline.

Combine a semantic (vector) index and a lexical (BM25) index:

  1. Query both indexes.
  2. Merge the two rankings with Reciprocal Rank Fusion (RRF):
         score(chunk) = sum over indexes of 1 / (k + rank)
  3. Optionally let Claude re-rank the merged shortlist.
  4. Answer from the best chunks.

Each index finds what the other misses, so the merged list is stronger.
"""

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = Anthropic()
MODEL = "claude-sonnet-5-5"
DIM = 256
RRF_K = 60

CHUNKS = [
    "Error E4021: the payment gateway rejected the card. Retry with another card.",
    "Refunds are returned to the original payment method within 5 business days.",
    "Express shipping takes 1 to 2 business days and costs 15 dollars extra.",
    "Standard shipping takes 3 to 5 business days and is free over 50 dollars.",
    "Devices include a 2 year limited warranty. Accidental damage is not covered.",
]


def text_of(message: Message) -> str:
    return "".join(b.text for b in message.content if b.type == "text")


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def vector_ranking(query: str, chunks: list[str]) -> list[int]:
    """Chunk indexes ordered by toy-embedding cosine similarity."""

    def embed(text: str) -> list[float]:
        vec = [0.0] * DIM
        for word in tokenize(text):
            vec[int(hashlib.md5(word.encode()).hexdigest(), 16) % DIM] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    q = embed(query)
    scores = [sum(a * b for a, b in zip(q, embed(c), strict=True)) for c in chunks]
    return sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)


def bm25_ranking(
    query: str, chunks: list[str], k1: float = 1.5, b: float = 0.75
) -> list[int]:
    """Chunk indexes ordered by BM25 score."""
    tokens = [tokenize(c) for c in chunks]
    avg_len = sum(len(t) for t in tokens) / len(tokens)
    doc_freq: Counter[str] = Counter()
    for t in tokens:
        doc_freq.update(set(t))

    def score(i: int) -> float:
        counts = Counter(tokens[i])
        total = 0.0
        for term in tokenize(query):
            tf = counts.get(term, 0)
            if tf:
                df = doc_freq[term]
                idf = math.log((len(chunks) - df + 0.5) / (df + 0.5) + 1)
                norm = tf + k1 * (1 - b + b * len(tokens[i]) / avg_len)
                total += idf * tf * (k1 + 1) / norm
        return total

    return sorted(range(len(chunks)), key=score, reverse=True)


def reciprocal_rank_fusion(rankings: list[list[int]]) -> list[int]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, index in enumerate(ranking, start=1):
            scores[index] = scores.get(index, 0.0) + 1 / (RRF_K + rank)
    return sorted(scores, key=lambda i: scores[i], reverse=True)


def rerank_with_claude(query: str, candidates: list[int]) -> list[int]:
    """Ask Claude to order the shortlist by relevance (returns chunk indexes)."""
    listing = "\n".join(f"[{i}] {CHUNKS[i]}" for i in candidates)
    message = client.messages.create(
        model=MODEL,
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": f"Question: {query}\n\nChunks:\n{listing}\n\n"
                "Return a JSON list of the chunk numbers, most relevant first.",
            },
            {"role": "assistant", "content": "```json"},
        ],
        stop_sequences=["\n```"],
    )
    raw = text_of(message).strip().removeprefix("```json").strip()
    order: list[int] = json.loads(raw)
    return [i for i in order if i in candidates]


if __name__ == "__main__":
    query = "E4021 payment failed"
    fused = reciprocal_rank_fusion(
        [vector_ranking(query, CHUNKS), bm25_ranking(query, CHUNKS)]
    )
    shortlist = fused[:3]
    print("fused shortlist:", shortlist)
    for i in rerank_with_claude(query, shortlist):
        print(f"  [{i}] {CHUNKS[i]}")
