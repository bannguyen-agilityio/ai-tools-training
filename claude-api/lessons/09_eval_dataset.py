"""Lessons 9-10: Prompt evaluation workflow + generating a test dataset.

Workflow: draft prompt -> build dataset -> run prompt on each case -> grade -> iterate.
Here we use Claude (with prefill + stop sequences, as in lesson 8) to generate
the dataset, then save it as JSON for the next lessons.
"""

import json
from pathlib import Path

from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = Anthropic()
MODEL = "claude-sonnet-5-5"
DATASET = Path(__file__).resolve().parent / "dataset.json"


def text_of(message: Message) -> str:
    return "".join(b.text for b in message.content if b.type == "text")


def generate_dataset(n: int = 3) -> list[dict]:
    """Ask Claude for n test cases: a task description + expected output format."""
    prompt = f"""Generate an evaluation dataset for a prompt that writes
AWS-related automation. Return a JSON array of {n} objects, each with:
- "task": a short description of what to produce
- "format": one of "python", "json", "regex"
Each task must be solvable with a single short snippet."""
    message = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "```json"},
        ],
        stop_sequences=["\n```"],
    )
    raw = text_of(message).strip().removeprefix("```json").strip()
    return json.loads(raw)


if __name__ == "__main__":
    cases = generate_dataset()
    DATASET.write_text(json.dumps(cases, indent=2))
    print(f"Wrote {len(cases)} cases to {DATASET.name}")
    for case in cases:
        print("-", case)
