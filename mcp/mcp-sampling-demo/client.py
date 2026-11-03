"""Test client for the sampling demo server (ported from the Claude Academy lesson).

Claude Desktop and Claude Code do not support MCP sampling, so this script acts
as the MCP client instead. It answers the server's sampling requests with a
simple function (`sampling_callback`) that calls Claude through the Anthropic SDK.

Set `ANTHROPIC_API_KEY` before running.

Changes from the lesson for the latest SDK (`mcp>=2.3.0`):
- `stdio_client` + `ClientSession` + `initialize()` is replaced by `Client`.
- `RequestContext` is now `ClientRequestContext`.

Usage: uv run client.py "text to summarize"
"""

import asyncio
import sys
from pathlib import Path

from anthropic import AsyncAnthropic, omit
from anthropic.types import MessageParam
from mcp.client import Client
from mcp.client.session import ClientRequestContext
from mcp.client.stdio import StdioServerParameters
from mcp.types import (
    CreateMessageRequestParams,
    CreateMessageResult,
    SamplingMessage,
    TextContent,
)

# Reads ANTHROPIC_API_KEY from the environment.
anthropic_client = AsyncAnthropic()
model = "claude-haiku-5-5"

# Start server.py as a subprocess and talk to it over stdio.
server_params = StdioServerParameters(
    command="uv",
    args=["run", "server.py"],
    # Resolve server.py next to this file, so the client works from any directory.
    cwd=Path(__file__).parent,
)


async def chat(
    input_messages: list[SamplingMessage],
    max_tokens: int,
    system_prompt: str | None = None,
) -> str:
    """Get an answer from Claude for the messages the server sent."""

    # Keep the text messages and their roles (user / assistant).
    # Each branch uses a literal role, because `MessageParam` is a union of
    # TypedDicts and a `Literal["user", "assistant"]` value matches none of them.
    messages: list[MessageParam] = []
    for msg in input_messages:
        if not isinstance(msg.content, TextContent):
            continue
        if msg.role == "user":
            messages.append({"role": "user", "content": msg.content.text})
        else:
            messages.append({"role": "assistant", "content": msg.content.text})
    if not messages:
        raise ValueError("The sampling request has no text to answer")

    response = await anthropic_client.messages.create(
        model=model,
        messages=messages,
        # Respect the limit the server asked for.
        max_tokens=max_tokens,
        # Forward the server's system prompt ("You are a helpful research assistant.").
        system=system_prompt or omit,
    )
    return "".join(block.text for block in response.content if block.type == "text")


async def sampling_callback(
    context: ClientRequestContext,
    params: CreateMessageRequestParams,
) -> CreateMessageResult:
    """Handle a sampling request from the server.

    Passing this function to `Client` is what makes the client declare the
    `sampling` capability, which the server needs.
    """

    # Log to stderr so it does not mix with the final result printed to stdout.
    print("[client] sampling request received -> calling Claude", file=sys.stderr)
    text = await chat(params.messages, params.max_tokens, params.system_prompt)

    # Wrap the answer in the result type the server expects.
    return CreateMessageResult(
        role="assistant",
        model=model,
        content=TextContent(type="text", text=text),
        stop_reason="endTurn",
    )


async def run(text: str) -> None:
    # Registering the callback is what declares the sampling capability.
    async with Client(server_params, sampling_callback=sampling_callback) as client:
        # The server sends a sampling request back to us during this call, and
        # `sampling_callback` answers it before the call returns.
        result = await client.call_tool("summarize", {"text_to_summarize": text})
        # A failed tool call still returns text (the error message), so check the flag.
        if result.is_error:
            raise RuntimeError(f"The summarize tool failed: {result.content}")
        # Tool results can hold images, audio or links too; `summarize` returns text.
        content = result.content[0]
        if isinstance(content, TextContent):
            print(content.text)
        else:
            raise TypeError(f"Expected text from the tool, got {content.type}")


if __name__ == "__main__":
    # Use the first command-line argument as the text, or a built-in sentence.
    asyncio.run(
        run(
            sys.argv[1]
            if len(sys.argv) > 1
            else "MCP sampling lets a server ask the client's LLM to generate text."
        )
    )
