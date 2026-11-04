"""Lesson 5: System prompts steer role and tone."""

from pathlib import Path

from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = Anthropic()
MODEL = "claude-sonnet-5-5"


def text_of(message: Message) -> str:
    return "".join(b.text for b in message.content if b.type == "text")


message = client.messages.create(
    model=MODEL,
    max_tokens=500,
    system=(
        "You are a patient math tutor. "
        "Guide with hints; never give the final answer directly."
    ),
    messages=[{"role": "user", "content": "How do I solve 5x + 2 = 17?"}],
)
print(text_of(message))
