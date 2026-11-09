"""Tool use: Project overview.

The running project is a small assistant that needs real-world abilities:
the current time, date arithmetic and reminders. Without tools Claude can only
guess, which is the problem the next lessons solve.
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


def chat(prompt: str) -> str:
    message = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return text_of(message)


if __name__ == "__main__":
    for prompt in (
        "What is the exact date and time right now?",
        "Set a reminder to submit my report in 3 days.",
    ):
        print(f"> {prompt}\n{chat(prompt)}\n")
