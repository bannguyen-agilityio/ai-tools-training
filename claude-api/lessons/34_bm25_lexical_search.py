"""RAG: BM25 lexical search.

Embeddings can miss exact terms (error codes, names, IDs). BM25 is the classic
keyword ranking: it scores a chunk higher when it contains the query's words,
especially rare ones (IDF), with diminishing returns for repeats and a penalty
for long chunks.

    score = sum over query terms of
            idf(t) * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len / avg_len))
"""

import math
import re
from collections import Counter

K1 = 1.5
B = 0.75


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class BM25:
    def __init__(self, documents: list[str]) -> None:
        self.documents = documents
        self.tokens = [tokenize(d) for d in documents]
        self.avg_len = sum(len(t) for t in self.tokens) / len(self.tokens)
        # Document frequency: in how many documents does each term appear?
        self.doc_freq: Counter[str] = Counter()
        for doc_tokens in self.tokens:
            self.doc_freq.update(set(doc_tokens))

    def idf(self, term: str) -> float:
        n = len(self.documents)
        df = self.doc_freq.get(term, 0)
        return math.log((n - df + 0.5) / (df + 0.5) + 1)

    def score(self, query: str, index: int) -> float:
        counts = Counter(self.tokens[index])
        length = len(self.tokens[index])
        total = 0.0
        for term in tokenize(query):
            tf = counts.get(term, 0)
            if tf == 0:
                continue
            norm = tf + K1 * (1 - B + B * length / self.avg_len)
            total += self.idf(term) * tf * (K1 + 1) / norm
        return total

    def search(self, query: str, k: int = 3) -> list[tuple[float, str]]:
        scored = [(self.score(query, i), d) for i, d in enumerate(self.documents)]
        return sorted(scored, reverse=True)[:k]


if __name__ == "__main__":
    docs = [
        "Error E4021: the payment gateway rejected the card.",
        "Payments are processed securely by our gateway provider.",
        "Refunds are returned to the original payment method.",
        "Express shipping takes 1 to 2 business days.",
    ]
    bm25 = BM25(docs)
    # An exact error code is a perfect fit for lexical search.
    for score, doc in bm25.search("E4021"):
        print(f"{score:.3f}  {doc}")
