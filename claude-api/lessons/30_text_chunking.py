"""RAG: Text chunking strategies.

Chunking splits a document into pieces small enough to retrieve precisely.
Three common strategies, each with different trade-offs:

- size-based: fixed length with overlap (simple, may cut mid-sentence)
- sentence-based: groups of whole sentences (keeps meaning intact)
- structure-based: split on headings (best when the document has structure)
"""

import re

DOCUMENT = """# Refunds
Customers may request a refund within 30 days. Refunds go to the original
payment method. Processing takes 5 business days.

# Shipping
Standard shipping takes 3 to 5 business days. Express takes 1 to 2 days.
Express costs 15 dollars extra.

# Warranty
Devices include a 2 year limited warranty. Accidental damage is not covered."""


def chunk_by_size(text: str, size: int = 120, overlap: int = 30) -> list[str]:
    """Fixed-size windows; overlap keeps context across the cut."""
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    step = size - overlap
    return [text[i : i + size] for i in range(0, len(text), step)]


def chunk_by_sentence(text: str, per_chunk: int = 2, overlap: int = 1) -> list[str]:
    """Groups of whole sentences, sliding by (per_chunk - overlap)."""
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    step = max(per_chunk - overlap, 1)
    return [
        " ".join(sentences[i : i + per_chunk]) for i in range(0, len(sentences), step)
    ]


def chunk_by_section(text: str) -> list[str]:
    """One chunk per markdown heading, heading included."""
    parts = re.split(r"(?m)^(?=# )", text)
    return [p.strip() for p in parts if p.strip()]


if __name__ == "__main__":
    strategies = {
        "size": chunk_by_size(DOCUMENT),
        "sentence": chunk_by_sentence(DOCUMENT),
        "section": chunk_by_section(DOCUMENT),
    }
    for name, chunks in strategies.items():
        print(f"== {name}: {len(chunks)} chunks")
        for chunk in chunks:
            print(f"  - {chunk!r}")
