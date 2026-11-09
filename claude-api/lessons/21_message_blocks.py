"""Tool use: Handling message blocks.

With tools, a reply's content is a list of blocks: usually a text block
followed by one or more tool_use blocks. Keep the whole assistant content in the
history; do not just keep the text.
"""

from pathlib import Path

from anthropic import Anthropic
from anthropic.types import MessageParam, ToolParam
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = Anthropic()
MODEL = "claude-sonnet-5-5"

GET_TIME_TOOL: ToolParam = {
    "name": "get_current_datetime",
    "description": "Returns the current date and time using a strftime format.",
    "input_schema": {
        "type": "object",
        "properties": {
            "date_format": {
                "type": "string",
                "description": "strftime format, e.g. '%Y-%m-%d %H:%M:%S'.",
            }
        },
    },
}

if __name__ == "__main__":
    messages: list[MessageParam] = [
        {"role": "user", "content": "What time is it? Check first, then answer."}
    ]
    message = client.messages.create(
        model=MODEL, max_tokens=500, tools=[GET_TIME_TOOL], messages=messages
    )

    for block in message.content:
        if block.type == "text":
            print("text    :", block.text)
        elif block.type == "tool_use":
            print("tool_use:", block.id, block.name, block.input)

    # Keep every block (text AND tool_use) so the next request stays valid.
    messages.append({"role": "assistant", "content": message.content})
    print("history roles:", [m["role"] for m in messages])
