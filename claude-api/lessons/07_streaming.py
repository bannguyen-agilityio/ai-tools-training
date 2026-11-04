"""Lesson 7: Response streaming, printing chunks as they arrive."""

from pathlib import Path

from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = Anthropic()
MODEL = "claude-sonnet-5-5"


def text_of(message: Message) -> str:
    return "".join(b.text for b in message.content if b.type == "text")


with client.messages.stream(
    model=MODEL,
    max_tokens=1000,
    messages=[{"role": "user", "content": "Write a short poem about the sea."}],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
    final = stream.get_final_message()
print("\n\nstop_reason:", final.stop_reason)
