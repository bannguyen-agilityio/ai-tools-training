"""Lesson 19: Provide examples (one-shot / multi-shot).

Show input/output pairs so Claude copies the format and judgment, including
tricky edge cases such as sarcasm.
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


PROMPT = """Classify the sentiment of the review as positive, negative or neutral.
Reply with the label only.

<example>
<review>Fast shipping and it works perfectly.</review>
<label>positive</label>
</example>
<example>
<review>Oh great, it broke after one day. Just what I wanted.</review>
<label>negative</label>
</example>
<example>
<review>It arrived on Tuesday.</review>
<label>neutral</label>
</example>

<review>Yeah, because waiting three weeks is totally my idea of fun.</review>"""

if __name__ == "__main__":
    print(ask(PROMPT))
