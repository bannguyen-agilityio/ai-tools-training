"""Tool use: Introducing tool use.

Claude cannot know the current time. With tool use we describe a function, Claude
asks us to run it (stop_reason == "tool_use"), and we feed the result back.
This script shows only the first half: Claude's request for a tool.
"""

from pathlib import Path

from anthropic import Anthropic
from anthropic.types import ToolParam
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = Anthropic()
MODEL = "claude-sonnet-5-5"

GET_TIME_TOOL: ToolParam = {
    "name": "get_current_datetime",
    "description": "Returns the current date and time.",
    "input_schema": {"type": "object", "properties": {}},
}

if __name__ == "__main__":
    message = client.messages.create(
        model=MODEL,
        max_tokens=500,
        tools=[GET_TIME_TOOL],
        messages=[{"role": "user", "content": "What time is it right now?"}],
    )
    # Claude does not run anything itself: it stops and asks us to.
    print("stop_reason:", message.stop_reason)
    for block in message.content:
        print(block)
