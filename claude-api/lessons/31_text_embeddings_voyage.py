"""RAG: Text embeddings with Voyage AI.

Same demo as 31_text_embeddings.py, but with real semantic embeddings from
Voyage AI (Anthropic's recommended embeddings provider).

Setup: put VOYAGE_API_KEY in .env (https://dash.voyageai.com), then
`uv sync --group voyage`.
"""

import voyageai
from dotenv import load_dotenv

load_dotenv()

MODEL = "voyage-3.5"

client = voyageai.Client()  # reads VOYAGE_API_KEY from the environment


def embed(texts: list[str], input_type: str) -> list[list[float]]:
    """Embed texts. input_type is "document" for stored text, "query" for searches."""
    result = client.embed(texts, model=MODEL, input_type=input_type)
    return result.embeddings


def cosine_similarity(a: list[float], b: list[float]) -> float:
    # Voyage embeddings are normalised to unit length, so dot product == cosine.
    return sum(x * y for x, y in zip(a, b, strict=True))


if __name__ == "__main__":
    query = "how long does express shipping take"
    texts = [
        "Express shipping takes 1 to 2 business days.",
        "Refunds are returned to the original payment method.",
        "The warranty covers manufacturing defects for 2 years.",
    ]
    query_vector = embed([query], "query")[0]
    print(f"dimensions: {len(query_vector)}")
    ranked = sorted(
        zip(
            (cosine_similarity(query_vector, v) for v in embed(texts, "document")),
            texts,
            strict=True,
        ),
        reverse=True,
    )
    for score, text in ranked:
        print(f"{score:.3f}  {text}")
