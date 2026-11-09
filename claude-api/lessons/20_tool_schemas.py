"""Tool use: Tool schemas.

A schema tells Claude what a tool does and what arguments it takes. Write a
detailed description (what, when to use, when not to) and describe every property.
"""

import json
from pathlib import Path

from anthropic import Anthropic
from anthropic.types import ToolParam
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = Anthropic()
MODEL = "claude-sonnet-5-5"

ADD_DURATION_TOOL: ToolParam = {
    "name": "add_duration_to_datetime",
    "description": (
        "Adds a duration (days, hours, minutes) to a datetime and returns the "
        "resulting datetime. Use it for questions like 'what is the date in 3 "
        "days?'. Do not use it to read the current time."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "datetime_str": {
                "type": "string",
                "description": "Start datetime as 'YYYY-MM-DD HH:MM:SS'.",
            },
            "days": {"type": "integer", "description": "Days to add. Default 0."},
            "hours": {"type": "integer", "description": "Hours to add. Default 0."},
            "minutes": {
                "type": "integer",
                "description": "Minutes to add. Default 0.",
            },
        },
        "required": ["datetime_str"],
    },
}

if __name__ == "__main__":
    message = client.messages.create(
        model=MODEL,
        max_tokens=500,
        tools=[ADD_DURATION_TOOL],
        messages=[
            {
                "role": "user",
                "content": "What is 2 days and 3 hours after 2026-03-01 09:00:00?",
            }
        ],
    )
    for block in message.content:
        if block.type == "tool_use":
            # Claude filled in arguments that match the schema.
            print(block.name, json.dumps(block.input))
