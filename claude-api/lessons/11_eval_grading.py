"""Lessons 12-14: Model-based grading, code-based grading, combining scores.

- Model grader: Claude returns strengths, weaknesses, reasoning and a 1-10 score.
- Code grader: deterministic syntax check for the expected format.
- Final score = mean of both, per case and overall.
"""

import ast
import json
import re
from pathlib import Path
from statistics import mean

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


def grade_by_model(case: dict, output: str) -> dict:
    """Model-based grading. Asking for reasoning first avoids a lazy ~6 score."""
    prompt = f"""Evaluate this solution.
Task: {case["task"]}
Solution:
{output}

Return JSON with keys: "strengths" (list), "weaknesses" (list),
"reasoning" (string), "score" (integer 1-10)."""
    message = client.messages.create(
        model=MODEL,
        max_tokens=800,
        messages=[
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "```json"},
        ],
        stop_sequences=["\n```"],
    )
    return json.loads(text_of(message).strip().removeprefix("```json").strip())


def grade_syntax(case: dict, output: str) -> int:
    """Code-based grading: 10 if the output parses in its format, else 0."""
    try:
        if case["format"] == "json":
            json.loads(output)
        elif case["format"] == "python":
            ast.parse(output)
        elif case["format"] == "regex":
            re.compile(output)
    except ValueError, SyntaxError, re.error:
        return 0
    return 10


if __name__ == "__main__":
    scores = []
    for case in json.loads(DATASET.read_text()):
        output = run_prompt(case)
        model_grade = grade_by_model(case, output)
        syntax = grade_syntax(case, output)
        final = mean([model_grade["score"], syntax])
        scores.append(final)
        print(
            f"{case['task']}\n  model={model_grade['score']} syntax={syntax}"
            f" final={final}\n  {model_grade['reasoning']}"
        )
    print(f"\nAverage score: {mean(scores):.2f}")
