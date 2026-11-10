"""RAG: Introducing Retrieval Augmented Generation.

Long documents do not always fit in a prompt, and a huge prompt is slower, costs
more and dilutes Claude's attention. RAG instead retrieves only the relevant
pieces of the document and puts just those in the prompt.

This script contrasts both approaches. Retrieval here is a crude word-overlap
score; the next lessons build the real thing.
"""

import re
from pathlib import Path

from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = Anthropic()
MODEL = "claude-sonnet-5-5"

DOCUMENT = """Refunds: Customers may request a refund within 30 days of purchase.
Refunds are returned to the original payment method within 5 business days.

Shipping: Standard shipping takes 3 to 5 business days. Express shipping takes
1 to 2 business days and costs 15 dollars extra.

Warranty: All devices include a 2 year limited warranty covering manufacturing
defects. Accidental damage is not covered.

Privacy: We never sell personal data. Account data is deleted within 30 days of
an account closure request."""


def text_of(message: Message) -> str:
    return "".join(b.text for b in message.content if b.type == "text")


def words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def retrieve(question: str, document: str) -> str:
    """Return the paragraph sharing the most words with the question."""
    paragraphs = [p.strip() for p in document.split("\n\n")]
    query = words(question)
    return max(paragraphs, key=lambda p: len(query & words(p)))


def ask(question: str, context: str) -> str:
    message = client.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": f"<context>\n{context}\n</context>\n\n"
                f"Answer using only the context.\nQuestion: {question}",
            }
        ],
    )
    return text_of(message)


if __name__ == "__main__":
    question = "How long does express shipping take?"
    chunk = retrieve(question, DOCUMENT)
    print(f"Whole document: {len(DOCUMENT)} chars | retrieved: {len(chunk)} chars")
    print(f"Retrieved: {chunk!r}\n")
    print(ask(question, chunk))
