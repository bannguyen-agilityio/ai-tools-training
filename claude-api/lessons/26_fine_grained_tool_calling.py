"""Tool use: Fine-grained tool calling.

When streaming, Claude normally buffers a tool's arguments until they form valid
JSON. With eager_input_streaming=True the argument chunks arrive immediately,
which lowers latency but means partial/invalid JSON is possible, so parse
only once the block is complete.
"""

import json
from pathlib import Path

from anthropic import Anthropic
from anthropic.types import ToolParam
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = Anthropic()
MODEL = "claude-sonnet-5-5"

SAVE_NOTE_TOOL: ToolParam = {
    "name": "save_note",
    "description": "Saves a note with a title and a long body.",
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "body": {"type": "string", "description": "The full note text."},
        },
        "required": ["title", "body"],
    },
    "eager_input_streaming": True,
}

if __name__ == "__main__":
    with client.messages.stream(
        model=MODEL,
        max_tokens=800,
        tools=[SAVE_NOTE_TOOL],
        tool_choice={"type": "tool", "name": "save_note"},
        messages=[
            {"role": "user", "content": "Save a short note about the history of tea."}
        ],
    ) as stream:
        for event in stream:
            if event.type == "input_json":
                # Raw argument fragments, as soon as Claude produces them.
                print(repr(event.partial_json))
        final = stream.get_final_message()

    tool_use = next(b for b in final.content if b.type == "tool_use")
    print("\nComplete input:", json.dumps(tool_use.input, indent=2))
