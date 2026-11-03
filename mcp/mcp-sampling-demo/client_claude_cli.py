"""Sampling client that answers with `claude -p`, so no API key is needed.

Same as `client.py`, except `sampling_callback` runs the Claude Code CLI instead
of calling the Anthropic SDK. It uses your existing Claude Code login, so
`claude` must be installed, logged in and on your `PATH`.

Usage: uv run client_claude_cli.py "text to summarize"
"""

import asyncio
import subprocess
import sys
from pathlib import Path

from mcp.client import Client
from mcp.client.session import ClientRequestContext
from mcp.client.stdio import StdioServerParameters
from mcp.types import (
    CreateMessageRequestParams,
    CreateMessageResult,
    SamplingMessage,
    TextContent,
)

# How long to wait for `claude -p` before giving up.
CLAUDE_TIMEOUT_SECONDS = 120

# Start server.py as a subprocess and talk to it over stdio.
server_params = StdioServerParameters(
    command="uv",
    args=["run", "server.py"],
    # Resolve server.py next to this file, so the client works from any directory.
    cwd=Path(__file__).parent,
)


def run_claude(cmd: list[str], prompt: str) -> str:
    """Run `claude`, send it the prompt on stdin, and return its output as text.

    The prompt goes through stdin, not the command line, so text that starts
    with `-` cannot be read as a flag.

    A separate function keeps the types exact: calling `subprocess.run` through
    `asyncio.to_thread` hides the `text=True` overload from the type checker, so
    it would infer `str | bytes | Any` for `stdout`.
    """

    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            check=True,
            timeout=CLAUDE_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "`claude` was not found. Install Claude Code and put it on your PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        # Show why `claude` failed (not logged in, ...), not just the exit code.
        raise RuntimeError(f"claude -p failed: {exc.stderr.strip()}") from exc
    return result.stdout.strip()


async def chat(
    input_messages: list[SamplingMessage], system_prompt: str | None = None
) -> str:
    """Get an answer from Claude for the messages the server sent."""

    # Join the text of the messages the server wants the LLM to answer.
    prompt = "\n".join(
        m.content.text for m in input_messages if isinstance(m.content, TextContent)
    )
    if not prompt:
        raise ValueError("The sampling request has no text to answer")

    # `claude -p` prints a single answer and exits (non-interactive mode).
    # `--tools ""` turns off all tools, so the answer is text only and the
    # server's text cannot make Claude read files or run commands.
    cmd = ["claude", "-p", "--tools", ""]
    if system_prompt:
        # Forward the server's system prompt ("You are a helpful research assistant.").
        cmd += ["--append-system-prompt", system_prompt]

    # subprocess.run blocks, so run it in a thread to keep the event loop free.
    return await asyncio.to_thread(run_claude, cmd, prompt)


async def sampling_callback(
    context: ClientRequestContext,
    params: CreateMessageRequestParams,
) -> CreateMessageResult:
    """Handle a sampling request from the server.

    Passing this function to `Client` is what makes the client declare the
    `sampling` capability, which the server needs. `claude -p` has no token
    limit option, so `params.max_tokens` is not applied here.
    """

    # Log to stderr so it does not mix with the final result printed to stdout.
    print("[client] sampling request received -> calling claude -p", file=sys.stderr)
    text = await chat(params.messages, params.system_prompt)

    # Wrap the answer in the result type the server expects.
    return CreateMessageResult(
        role="assistant",
        model="claude-code",
        content=TextContent(type="text", text=text),
        stop_reason="endTurn",
    )


async def progress_callback(
    progress: float, total: float | None, message: str | None
) -> None:
    """Print a progress update sent by the server (`ctx.report_progress(...)`).

    Show a percentage when the server gave a total, otherwise the raw value.
    """

    shown = f"{progress / total:.0%}" if total else f"{progress:g}"
    print(f"[progress] {shown} {message or ''}".rstrip(), file=sys.stderr)


async def run(text: str) -> None:
    # Registering the callback is what declares the sampling capability.
    async with Client(
        server_params,
        sampling_callback=sampling_callback,
    ) as client:
        # The server sends a sampling request back to us during this call, and
        # `sampling_callback` answers it before the call returns.
        # `progress_callback` is passed per call, not per session.
        result = await client.call_tool(
            "summarize",
            {"text_to_summarize": text},
            progress_callback=progress_callback,
        )
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
