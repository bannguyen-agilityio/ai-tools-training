"""MCP server for the sampling demo (ported from the Claude Academy lesson).

Sampling means the server asks the *client's* LLM to generate text, so the
server needs no API key of its own. The client must declare the `sampling`
capability when it connects. Claude Desktop and Claude Code currently do not,
so run this with `client.py` (or the MCP Inspector).

Changes from the lesson for the latest SDK (`mcp>=2.3.0`):
- `FastMCP` is now `MCPServer`, imported from `mcp.server.mcpserver`.
- `await ctx.session.create_message(...)` no longer works: a tool cannot send a
  request to the client in the middle of its own run. Instead the tool declares
  what it needs with `Resolve(...)`, the SDK sends the `Sample` request to the
  client, and the LLM's reply is passed into the tool as an argument.
"""

from typing import Annotated

from mcp.server.mcpserver import MCPServer, Resolve, Sample
from mcp.types import CreateMessageResult, SamplingMessage, TextContent

# The name shown to clients.
mcp = MCPServer(name="Demo Server")


def build_summary_request(text_to_summarize: str) -> Sample:
    """Build the sampling request sent to the client's LLM.

    This is a *resolver*: the SDK calls it with the tool's arguments (same
    names as in `summarize`) and sends the returned `Sample` to the client.
    """

    # The instructions the client's LLM should follow.
    prompt = f"""
        Please summarize the following text:
        {text_to_summarize}
    """

    return Sample(
        messages=[
            SamplingMessage(role="user", content=TextContent(type="text", text=prompt))
        ],
        # Upper limit on the length of the generated answer.
        max_tokens=4000,
        # Sets the LLM's role for this request.
        system_prompt="You are a helpful research assistant.",
    )


@mcp.tool()
async def summarize(
    text_to_summarize: str,
    # `Resolve` makes the SDK run `build_summary_request`, send the sampling
    # request to the client, and inject the LLM's reply here as `result`.
    # The caller does not pass `result` in. If the client did not declare the
    # sampling capability, the call fails with error -32021 before this runs.
    result: Annotated[CreateMessageResult, Resolve(build_summary_request)],
) -> str:
    """Summarize text using the connected client's LLM (via sampling)."""

    # The client may reply with images or audio; this tool only accepts text.
    if result.content.type == "text":
        return result.content.text
    raise ValueError("Sampling failed")


if __name__ == "__main__":
    # Run over stdio. Never print to stdout here: it carries the MCP protocol
    # messages. Write logs to stderr instead.
    mcp.run(transport="stdio")
