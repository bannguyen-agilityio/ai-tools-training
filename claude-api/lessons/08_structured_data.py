"""Lesson 8: Structured data via assistant prefill + stop sequences."""

import json
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
    messages=[
        {
            "role": "user",
            "content": "Write a tiny JSON config for a web server (host, port, debug).",
        },
        # Prefill: Claude continues from here, so it starts straight into the JSON.
        {"role": "assistant", "content": "```json"},
    ],
    # Stop at the closing fence so only the JSON is returned. "\n```" (not "```")
    # so a reply that echoes the opening fence is not cut off at character 0.
    stop_sequences=["\n```"],
)

raw = text_of(message).strip()
# Some backends echo the prefill instead of continuing it; drop it if present.
raw = raw.removeprefix("```json").strip()
print(json.loads(raw))
