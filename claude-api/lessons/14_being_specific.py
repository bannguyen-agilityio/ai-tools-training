"""Lesson 17: Be specific.

Add guidelines (constraints on the output) or steps (how to reason) so Claude
does not have to guess what you want.
"""

from pathlib import Path

from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = Anthropic()
MODEL = "claude-sonnet-5-5"


def text_of(message: Message) -> str:
    return "".join(b.text for b in message.content if b.type == "text")


def ask(prompt: str) -> str:
    message = client.messages.create(
        model=MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    return text_of(message)


QUESTION = "Should a small team adopt microservices?"

GUIDELINES = f"""{QUESTION}

Follow these guidelines:
- Answer in at most 4 sentences.
- Give one concrete risk and one concrete benefit.
- End with a clear yes or no."""

STEPS = f"""{QUESTION}

Work through these steps:
1. List the team-size factors that matter.
2. Weigh operational cost against flexibility.
3. State your recommendation."""

if __name__ == "__main__":
    print("=== guidelines ===\n" + ask(GUIDELINES))
    print("\n=== steps ===\n" + ask(STEPS))
