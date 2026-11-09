"""Tool use: Using multiple tools.

Add more tools by adding a schema and a function, then dispatch by name. Errors
are returned with is_error=True so Claude can see what went wrong and retry.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

from anthropic import Anthropic
from anthropic.types import Message, MessageParam, ToolParam, ToolResultBlockParam
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = Anthropic()
MODEL = "claude-sonnet-5-5"
FMT = "%Y-%m-%d %H:%M:%S"


def get_current_datetime() -> str:
    return datetime.now().strftime(FMT)


def add_duration_to_datetime(datetime_str: str, days: int = 0, hours: int = 0) -> str:
    start = datetime.strptime(datetime_str, FMT)
    return (start + timedelta(days=days, hours=hours)).strftime(FMT)


def set_reminder(content: str, timestamp: str) -> str:
    datetime.strptime(timestamp, FMT)  # raises ValueError on a bad timestamp
    return f"Reminder set for {timestamp}: {content}"


FUNCTIONS = {
    "get_current_datetime": get_current_datetime,
    "add_duration_to_datetime": add_duration_to_datetime,
    "set_reminder": set_reminder,
}

TOOLS: list[ToolParam] = [
    {
        "name": "get_current_datetime",
        "description": "Returns the current date and time as 'YYYY-MM-DD HH:MM:SS'.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "add_duration_to_datetime",
        "description": "Adds days and/or hours to a 'YYYY-MM-DD HH:MM:SS' datetime.",
        "input_schema": {
            "type": "object",
            "properties": {
                "datetime_str": {"type": "string"},
                "days": {"type": "integer"},
                "hours": {"type": "integer"},
            },
            "required": ["datetime_str"],
        },
    },
    {
        "name": "set_reminder",
        "description": "Sets a reminder for a specific 'YYYY-MM-DD HH:MM:SS' time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "What to remind."},
                "timestamp": {"type": "string", "description": "When to remind."},
            },
            "required": ["content", "timestamp"],
        },
    },
]


def text_of(message: Message) -> str:
    return "".join(b.text for b in message.content if b.type == "text")


def run_tools(message: Message) -> list[ToolResultBlockParam]:
    """Run every tool_use block; one tool_result per block, errors flagged."""
    results: list[ToolResultBlockParam] = []
    for block in message.content:
        if block.type != "tool_use":
            continue
        try:
            args = cast(dict[str, Any], block.input)
            output, is_error = FUNCTIONS[block.name](**args), False
        except Exception as exc:
            output, is_error = str(exc), True
        results.append(
            {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": str(output),
                "is_error": is_error,
            }
        )
    return results


def run_conversation(prompt: str) -> str:
    messages: list[MessageParam] = [{"role": "user", "content": prompt}]
    while True:
        reply = client.messages.create(
            model=MODEL, max_tokens=800, tools=TOOLS, messages=messages
        )
        messages.append({"role": "assistant", "content": reply.content})
        if reply.stop_reason != "tool_use":
            return text_of(reply)
        messages.append({"role": "user", "content": run_tools(reply)})


if __name__ == "__main__":
    print(run_conversation("Remind me to submit my report in 3 days."))
