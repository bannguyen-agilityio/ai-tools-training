"""Lesson 4: Multi-turn conversations. The API is stateless: resend the history."""

from pathlib import Path

from anthropic import Anthropic
from anthropic.types import Message, MessageParam
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = Anthropic()
MODEL = "claude-sonnet-5-5"


def text_of(message: Message) -> str:
    return "".join(b.text for b in message.content if b.type == "text")


messages: list[MessageParam] = []


def chat(text: str) -> str:
    messages.append({"role": "user", "content": text})
    reply = client.messages.create(model=MODEL, max_tokens=500, messages=messages)
    answer = text_of(reply)
    messages.append({"role": "assistant", "content": answer})
    return answer


print(chat("Define quantum computing in one sentence."))
print(chat("Write another sentence."))
