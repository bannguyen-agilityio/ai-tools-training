# MCP Sampling Demo

A minimal MCP server that uses **sampling**: the server asks the *client's* LLM to generate text, so the server needs no API key of its own.

| File | Role |
|---|---|
| `server.py` | MCP server with one tool, `summarize(text_to_summarize)`. It sends a sampling request and returns the client's answer. |
| `client.py` | Test client. Its `sampling_callback` function answers the server's request by calling Claude with the Anthropic SDK. Needs an API key. |
| `client_claude_cli.py` | Same client, but it answers with `claude -p` (Claude Code CLI). No API key needed. |

> **Claude Desktop and Claude Code do not support sampling.** They don't declare the `sampling` capability, so `summarize` fails in both. That is why `client.py` acts as the MCP client: it handles the sampling request with a simple function that calls Claude. See [Why not Claude Desktop or Claude Code?](#why-not-claude-desktop-or-claude-code).

## 1. Setup

**Requirements**

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- **One** of these, depending on the client you use:
  - An [Anthropic API key](https://console.anthropic.com/) for `client.py`, which calls Claude through the Anthropic SDK.
  - [Claude Code](https://claude.com/claude-code), installed and logged in, with `claude` on your `PATH`, for `client_claude_cli.py`. No API key is needed.

**Install**

```bash
cd mcp/mcp-sampling-demo
uv sync
```

**Set your API key** (only for `client.py`)

```bash
export ANTHROPIC_API_KEY="your-key"
```

**Check Claude Code** (only for `client_claude_cli.py`)

```bash
claude --version
```

## 2. Run

Run a client with the text you want summarized. It starts `server.py` for you, so you don't start the server separately.

With an API key:

```bash
uv run client.py "The Model Context Protocol lets servers expose tools to LLM clients. Sampling lets a server ask the client's model to generate text, so the server needs no API key of its own."
```

Without an API key, using Claude Code:

```bash
uv run client_claude_cli.py "The Model Context Protocol lets servers expose tools to LLM clients. Sampling lets a server ask the client's model to generate text, so the server needs no API key of its own."
```

Without an argument, either client summarizes a built-in sentence.

## 3. Test

**Expected output**

```
[client] sampling request received -> calling Claude   (or "calling claude -p")
[server log] info: Sampling finished, got a text reply
[progress] 50% Checking the reply
[progress] 100% Summary ready
<a short summary of your text, written by Claude>
```

The lines that start with `[...]` go to stderr. `[client]` shows that the server's sampling request reached the client, and `[server log]` and `[progress]` are the notifications described [below](#log-and-progress-notifications). The last line is the summary returned by the `summarize` tool. The wording of the summary differs on each run.

**Checks**

| What you see | Meaning |
|---|---|
| `[client] sampling request received` and a summary | Works: the server sent a sampling request and the client answered it. |
| No `[client] ...` line, and an error | The server never reached the client. Check `uv sync` ran and `server.py` starts. |
| `Could not resolve authentication method` | `client.py` needs `ANTHROPIC_API_KEY`. Export it, or use `client_claude_cli.py`. |
| `` `claude` was not found `` | `client_claude_cli.py` needs Claude Code on your `PATH`. |
| `claude -p failed: ...` | The message after the colon is the CLI's own error, for example not logged in. Run `claude` once to log in. |

**Try it with other text**

```bash
uv run client.py "Your own paragraph here."
```

### How it works

1. The client (`client.py` or `client_claude_cli.py`) starts `server.py` over stdio and declares the `sampling` capability by passing `sampling_callback`.
2. It calls the `summarize` tool.
3. The server's `Resolve(...)` step sends a sampling request back to the client (the `[client] sampling request received` line).
4. `sampling_callback` sends the server's messages and system prompt to Claude. `client.py` uses the Anthropic SDK and the `max_tokens` the server asked for. `client_claude_cli.py` runs `claude -p` with tools off and the prompt on stdin; the CLI has no token limit option, so `max_tokens` is not applied.
5. The client returns Claude's answer to the server, and the tool returns it as the result.

## Log and progress notifications

`summarize` also sends two kinds of notifications while it runs, following the Claude Academy [log and progress lesson](https://academy.claude.com/courses/model-context-protocol-advanced-topics/log-and-progress-notifications):

| | Server (`server.py`) | Client (both clients) |
|---|---|---|
| Log message | `await ctx.info("...")` | `logging_callback`, passed to `Client(...)` together with `log_level="info"` |
| Progress | `await ctx.report_progress(progress, total, message)` | `progress_callback`, passed to each `client.call_tool(...)` |

Differences from the lesson in the latest SDK:

- `ctx` is the tool's `Context` argument, imported from `mcp.server.mcpserver`.
- The client must opt in to logs with `log_level="info"`. A `logging_callback` alone receives nothing.
- `progress_callback` is passed per `call_tool`, not per session. The client prints a percentage when the server gives a total, and the raw value otherwise.
- Logging is deprecated in the 2026-07-28 MCP spec, and the SDK warns about `ctx.info` with an `MCPDeprecationWarning`. `server.py` hides that one warning because the demo uses logging on purpose; remove the `warnings.filterwarnings(...)` line if you drop `ctx.info`. Progress is not deprecated.
- The sampling request runs before the tool body starts, because `Resolve` runs first. The notifications here therefore report what happens after sampling, not the sampling itself.

## Why not Claude Desktop or Claude Code?

Neither declares the `sampling` capability, so calling `summarize` from either one fails:

```
Client did not declare the sampling capability required by resolver 'build_summary_request'
```

In Claude Desktop this shows as "The connector returned an error or an invalid response" (MCP error `-32021`, missing required client capability). The summary is still written by Claude, but the MCP client has to be our own script.

Sampling is also deprecated in the 2026-07-28 revision of the MCP spec, so treat this as a demo.

## Changes from the Claude Academy lesson

`server.py` and `client.py` are ported from the [sampling walkthrough](https://academy.claude.com/courses/model-context-protocol-advanced-topics/sampling-walkthrough) to the latest SDK (`mcp>=2.3.0`):

| Lesson | Latest SDK |
|---|---|
| `FastMCP` | `MCPServer` (`from mcp.server.mcpserver import MCPServer`) |
| `await ctx.session.create_message(...)` inside the tool | Fails with "no back-channel". Use `Resolve(...)` + `Sample(...)`: the SDK sends the request and passes the reply into the tool as an argument. |
| `stdio_client` + `ClientSession` + `initialize()` | `Client(server_params, sampling_callback=...)` |
| `RequestContext` | `ClientRequestContext` |
| Anthropic API call in the client | Same: `AsyncAnthropic().messages.create(...)`, with model `claude-haiku-5-5` |

## Optional: MCP Inspector

The Inspector is another client with sampling support (not tested for this demo):

```bash
uv run mcp dev server.py
```

Open the printed URL, go to **Tools → summarize**, run it, and approve the request in the **Sampling** tab.

## Optional: register in Claude Desktop

You can register the server in Claude Desktop to see it connect, but `summarize` fails there for the reason above. Edit `claude_desktop_config.json` and restart Desktop from the system tray:

```json
{
  "mcpServers": {
    "Sampling Demo": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-sampling-demo", "server.py"]
    }
  }
}
```

The server then appears under **Settings → Desktop app → Extension → Local MCP servers**. The Microsoft Store version of Desktop keeps the file at `%LOCALAPPDATA%\Claude-Data\<package id>\claude_desktop_config.json`.

On Windows with WSL, Desktop runs on Windows, so use `wsl.exe` as the command and run `uv` inside WSL, with the full path to `uv`:

```json
{
  "mcpServers": {
    "Sampling Demo": {
      "command": "wsl.exe",
      "args": [
        "-e",
        "bash",
        "-lc",
        "cd /path/to/mcp-sampling-demo && /full/path/to/uv run server.py"
      ]
    }
  }
}
```

## Troubleshooting

| Problem | Fix |
|---|---|
| `Client did not declare the sampling capability` | Expected in Claude Desktop and Claude Code. Use `client.py` instead. |
| `uv: command not found` | Install [uv](https://docs.astral.sh/uv/), or use its full path. |
| Desktop shows no server | Quit Desktop from the system tray and reopen it; it only reads the config at startup. |
| Desktop server fails to start | Use the full path to `uv` in the config. Check `Claude\logs\mcp-server-Sampling Demo.log`. |
