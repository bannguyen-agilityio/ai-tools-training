"""Lesson 6: Temperature (0.0 predictable ... 1.0 creative)."""

from pathlib import Path

from anthropic import Anthropic
from anthropic.types import Message, MessageParam
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = Anthropic()
MODEL = "claude-sonnet-5-5"


def text_of(message: Message) -> str:
    return "".join(b.text for b in message.content if b.type == "text")


prompt: list[MessageParam] = [
    {"role": "user", "content": "Suggest a name for a coffee shop. Name only."}
]
for temp in (0.0, 1.0):
    message = client.messages.create(
        model=MODEL,
        max_tokens=100,
        extra_body={"temperature": temp},  # not a typed param in this SDK
        messages=prompt,
    )
    print(f"temperature={temp}: {text_of(message)}")
