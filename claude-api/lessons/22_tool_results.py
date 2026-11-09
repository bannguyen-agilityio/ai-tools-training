"""Tool use: Sending tool results.

After running the tool, reply with a *user* message holding a tool_result block.
Its tool_use_id must match the tool_use block it answers. Claude then writes the
final answer.
"""

from datetime import datetime
from pathlib import Path

from anthropic import Anthropic
from anthropic.types import Message, MessageParam, ToolParam
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = Anthropic()
MODEL = "claude-sonnet-5-5"

GET_TIME_TOOL: ToolParam = {
    "name": "get_current_datetime",
    "description": "Returns the current date and time as 'YYYY-MM-DD HH:MM:SS'.",
    "input_schema": {"type": "object", "properties": {}},
}


def text_of(message: Message) -> str:
    return "".join(b.text for b in message.content if b.type == "text")


if __name__ == "__main__":
    messages: list[MessageParam] = [
        {"role": "user", "content": "What is today's date?"}
    ]
    first = client.messages.create(
        model=MODEL, max_tokens=500, tools=[GET_TIME_TOOL], messages=messages
    )
    messages.append({"role": "assistant", "content": first.content})

    tool_use = next(b for b in first.content if b.type == "tool_use")
    result = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result,
                }
            ],
        }
    )
    # tools= must be sent again: the history contains tool blocks.
    final = client.messages.create(
        model=MODEL, max_tokens=500, tools=[GET_TIME_TOOL], messages=messages
    )
    print(text_of(final))
