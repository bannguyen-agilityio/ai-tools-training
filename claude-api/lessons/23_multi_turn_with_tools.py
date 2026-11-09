"""Tool use: Multi-turn conversations with tools.

Claude may call a tool, read the result, then call another one before answering.
So we cannot assume one request/response: we keep appending to the history and
ask again. Small helpers keep the history handling tidy.
"""

from datetime import datetime, timedelta
from pathlib import Path

from anthropic import Anthropic
from anthropic.types import Message, MessageParam, ToolParam
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


def add_user_message(messages: list[MessageParam], content) -> None:
    messages.append({"role": "user", "content": content})


def add_assistant_message(messages: list[MessageParam], message: Message) -> None:
    messages.append({"role": "assistant", "content": message.content})


def chat(messages: list[MessageParam]) -> Message:
    return client.messages.create(
        model=MODEL, max_tokens=500, tools=TOOLS, messages=messages
    )


if __name__ == "__main__":
    messages: list[MessageParam] = []
    add_user_message(messages, "What will the date be in 10 days?")
    reply = chat(messages)
    add_assistant_message(messages, reply)

    # The first reply is only the first step: it asks for the current time.
    print("stop_reason:", reply.stop_reason)
    for block in reply.content:
        if block.type == "tool_use":
            print("requested:", block.name, block.input)
            now = datetime.now().strftime(FMT)
            add_user_message(
                messages,
                [{"type": "tool_result", "tool_use_id": block.id, "content": now}],
            )

    # Claude now needs a second tool (add_duration_to_datetime) to finish.
    reply = chat(messages)
    add_assistant_message(messages, reply)
    print("stop_reason:", reply.stop_reason)
    for block in reply.content:
        if block.type == "tool_use":
            args: dict = dict(block.input)
            start = datetime.strptime(args["datetime_str"], FMT)
            end = (start + timedelta(days=args["days"])).strftime(FMT)
            print("requested:", block.name, block.input, "->", end)
