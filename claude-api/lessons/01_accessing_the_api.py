"""Lesson 1: Accessing the API. Client -> API server -> Claude -> response."""

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
    max_tokens=200,
    messages=[
        {"role": "user", "content": "In one sentence, how does a client reach Claude?"}
    ],
)
print(text_of(message))
