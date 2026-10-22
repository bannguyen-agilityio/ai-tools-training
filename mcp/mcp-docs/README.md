# mcp-docs

A small [FastMCP](https://gofastmcp.com) project: an MCP server that exposes an in-memory set of documents, and a client that exercises it.

| File        | Role                                                        |
| ----------- | ----------------------------------------------------------- |
| `server.py` | MCP server (`DocumentMCP`) with tools, a prompt and resources |
| `client.py` | Client that connects to the server and calls everything     |
| `main.py`   | Entry point that runs the client demo                       |

## What the server exposes

- **Tools**
  - `read_doc_contents(doc_id)`: return a document's contents.
  - `edit_document(doc_id, old_str, new_str)`: replace a string in a document.
- **Prompt**
  - `format(doc_id)`: asks the model to rewrite a document in Markdown.
- **Resources**
  - `docs://documents`: JSON list of document ids.
  - `docs://documents/{doc_id}`: plain-text contents of one document.

Documents live in memory, so edits last only for the lifetime of the server process.

## Prerequisites

- Python 3.14 (see `.python-version`)
- [uv](https://docs.astral.sh/uv/)
- Node.js, only needed for the Inspector

Install dependencies:

```bash
uv sync
```

## Run the server

```bash
uv run server.py
```

The server uses the default **stdio** transport, so it prints nothing and waits for an MCP client on stdin. This is expected. It is mainly meant to be launched by a client or the Inspector, not used by hand. Stop it with `Ctrl+C`.

## Run the client

```bash
uv run main.py
```

You don't need to start the server first. `client.py` creates `Client("server.py")`, which launches the server as a subprocess over stdio and shuts it down when the client exits.

The demo lists the tools, reads and edits `plan.md`, reads both resources, lists and fetches the `format` prompt, and finally shows the error raised when reading a document that doesn't exist.

To run the client module directly instead:

```bash
uv run client.py
```

## Debug with the MCP Inspector

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) is a web UI for trying out a server's tools, prompts and resources.

```bash
uv run fastmcp dev inspector server.py
```

FastMCP starts the server and launches the Inspector for it (this needs Node.js, since it runs the Inspector through `npx`). The terminal output includes a URL with a session token. Open that URL if the browser doesn't launch on its own. Auto-reload is on by default, so the server restarts when you edit its files. Add `--no-reload` to turn that off.

Useful options: `--ui-port` and `--server-port` change the Inspector's ports, and `--inspector-version` pins its version.

In the Inspector:

1. Make sure the transport is **STDIO**, then click **Connect**. FastMCP pre-fills the command and arguments.
2. **Tools** tab: list tools, then run `read_doc_contents` with `doc_id` set to `plan.md`.
3. **Prompts** tab: run `format` with a `doc_id`.
4. **Resources** tab: read `docs://documents`, or use the template for `docs://documents/{doc_id}`.

Run the Inspector from this directory so `server.py` and the `uv` environment resolve correctly.
