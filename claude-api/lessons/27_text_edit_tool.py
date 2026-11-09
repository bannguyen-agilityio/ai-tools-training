"""Tool use: The text edit tool.

Claude ships a built-in schema for file editing (str_replace_based_edit_tool), but
it only *requests* edits: we implement the commands. Here they run inside a
temporary directory so Claude cannot touch anything else.
"""

import tempfile
from pathlib import Path

from anthropic import Anthropic
from anthropic.types import Message, MessageParam, ToolTextEditor20250728Param
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = Anthropic()
MODEL = "claude-sonnet-5-5"

EDITOR_TOOL: ToolTextEditor20250728Param = {
    "type": "text_editor_20250728",
    "name": "str_replace_based_edit_tool",
}


def text_of(message: Message) -> str:
    return "".join(b.text for b in message.content if b.type == "text")


def run_editor(root: Path, args: dict) -> str:
    path = (root / args["path"].lstrip("/")).resolve()
    if not path.is_relative_to(root):
        return "Error: path is outside the workspace"
    match args["command"]:
        case "view":
            if not path.exists():
                return f"Error: {args['path']} does not exist"
            return path.read_text()
        case "str_replace":
            text = path.read_text()
            if text.count(args["old_str"]) != 1:
                return "Error: old_str must match exactly once"
            path.write_text(text.replace(args["old_str"], args["new_str"]))
            return "Edit applied"
        case "create":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(args["file_text"])
            return "File created"
        case "insert":
            lines = path.read_text().splitlines(keepends=True)
            lines.insert(args["insert_line"], args["insert_text"] + "\n")
            path.write_text("".join(lines))
            return "Text inserted"
    return f"Error: unsupported command {args['command']}"


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        (root / "greet.py").write_text("def greet(name):\n    print('Helo', name)\n")

        messages: list[MessageParam] = [
            {"role": "user", "content": "Fix the typo in greet.py, then confirm."}
        ]
        while True:
            reply = client.messages.create(
                model=MODEL, max_tokens=1000, tools=[EDITOR_TOOL], messages=messages
            )
            messages.append({"role": "assistant", "content": reply.content})
            if reply.stop_reason != "tool_use":
                break
            results = []
            for block in reply.content:
                if block.type == "tool_use":
                    print("command:", block.input)
                    results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": run_editor(root, dict(block.input)),
                        }
                    )
            messages.append({"role": "user", "content": results})

        print(text_of(reply))
        print("--- greet.py ---")
        print((root / "greet.py").read_text())
