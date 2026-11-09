"""Tool use: Implementing multiple turns.

Loop until Claude stops asking for tools: while stop_reason == "tool_use", run
the requested tools, send the results back, and call again.
"""

from datetime import datetime, timedelta
from pathlib import Path

from anthropic import Anthropic
from anthropic.types import (
    Message,
    MessageParam,
    ToolParam,
    ToolResultBlockParam,
)
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = Anthropic()
MODEL = "claude-sonnet-5-5"
FMT = "%Y-%m-%d %H:%M:%S"

TOOLS: list[ToolParam] = [
    {
        "name": "get_current_datetime",
        "description": "Returns the current date and time as 'YYYY-MM-DD HH:MM:SS'.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "add_duration_to_datetime",
        "description": "Adds days to a 'YYYY-MM-DD HH:MM:SS' datetime.",
        "input_schema": {
            "type": "object",
            "properties": {
                "datetime_str": {"type": "string"},
                "days": {"type": "integer"},
            },
            "required": ["datetime_str", "days"],
        },
    },
]


def text_of(message: Message) -> str:
    return "".join(b.text for b in message.content if b.type == "text")


def run_tool(name: str, tool_input: dict) -> str:
    if name == "get_current_datetime":
        return datetime.now().strftime(FMT)
    if name == "add_duration_to_datetime":
        start = datetime.strptime(tool_input["datetime_str"], FMT)
        return (start + timedelta(days=tool_input["days"])).strftime(FMT)
    raise ValueError(f"Unknown tool: {name}")


def run_conversation(prompt: str) -> str:
    messages: list[MessageParam] = [{"role": "user", "content": prompt}]
    while True:
        reply = client.messages.create(
            model=MODEL, max_tokens=500, tools=TOOLS, messages=messages
        )
        messages.append({"role": "assistant", "content": reply.content})
        if reply.stop_reason != "tool_use":
            return text_of(reply)

        results: list[ToolResultBlockParam] = []
        for block in reply.content:
            if block.type == "tool_use":
                print(f"  tool: {block.name} {block.input}")
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": run_tool(block.name, block.input),
                    }
                )
        messages.append({"role": "user", "content": results})


if __name__ == "__main__":
    print(run_conversation("What will the date be in 10 days?"))
