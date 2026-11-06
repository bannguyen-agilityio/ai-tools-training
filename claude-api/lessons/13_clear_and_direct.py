"""Lesson 16: Be clear and direct.

Lead with an action verb and state the task plainly, instead of hiding it in a
vague question.
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


VAGUE = "I was thinking about solar panels, what is the deal with them?"
DIRECT = "Write three bullet points explaining how solar panels generate electricity."

if __name__ == "__main__":
    print("=== vague ===\n" + ask(VAGUE))
    print("\n=== clear and direct ===\n" + ask(DIRECT))
