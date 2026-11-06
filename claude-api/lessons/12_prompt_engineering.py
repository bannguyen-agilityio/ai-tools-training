"""Lesson 15: Prompt engineering is iterative.

Start with a naive prompt, observe the output, then refine it. Each pass adds
one improvement; compare the results side by side.
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


PROMPTS = {
    "v1 naive": "Tell me about a healthy diet for athletes.",
    "v2 refined": (
        "Write a one-day meal plan for a marathon runner. "
        "Include breakfast, lunch, dinner, and a snack, with approximate calories."
    ),
}

if __name__ == "__main__":
    for name, prompt in PROMPTS.items():
        print(f"=== {name} ===\n{ask(prompt)}\n")
