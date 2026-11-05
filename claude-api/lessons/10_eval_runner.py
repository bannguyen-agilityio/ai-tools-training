"""Lesson 11: Running the eval (prompt template + per-case results)."""

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


def run_prompt(case: dict) -> str:
    """The prompt under test. Improve this and re-run to compare scores."""
    message = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": f"Please solve the task: {case['task']}\n"
                f"Respond with only {case['format']}, no explanation.",
            },
            {"role": "assistant", "content": "```code"},
        ],
        stop_sequences=["\n```"],
    )
    return text_of(message).strip().removeprefix("```code").strip()


def run_eval(cases: list[dict]) -> list[dict]:
    return [{"case": c, "output": run_prompt(c)} for c in cases]


if __name__ == "__main__":
    results = run_eval(json.loads(DATASET.read_text()))
    for r in results:
        print(f"TASK: {r['case']['task']}\nOUTPUT:\n{r['output']}\n")
