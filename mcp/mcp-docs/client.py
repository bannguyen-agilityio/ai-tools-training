import asyncio
import json
from typing import Any

from fastmcp import Client
from fastmcp.exceptions import ToolError
from mcp.types import TextContent, TextResourceContents

client = Client("server.py")


async def read_doc(doc_id: str) -> str:
    result = await client.call_tool("read_doc_contents", {"doc_id": doc_id})
    content = result.content[0]
    assert isinstance(content, TextContent)
    return content.text


async def edit_doc(doc_id: str, old_str: str, new_str: str) -> None:
    await client.call_tool(
        "edit_document",
        {"doc_id": doc_id, "old_str": old_str, "new_str": new_str},
    )


async def read_resource(uri: str) -> Any:
    resource = (await client.read_resource(uri))[0]
    assert isinstance(resource, TextResourceContents)

    if resource.mime_type == "application/json":
        return json.loads(resource.text)

    return resource.text


async def main():
    # One session for everything, so edits persist between calls.
    async with client:
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

        doc_id = "plan.md"

        print(f"\n[READ] {doc_id}")
        print(f"  {await read_doc(doc_id)}")

        old, new = "implementation", "deployment"
        print(f"\n[EDIT] {doc_id}: replace {old!r} -> {new!r}")
        await edit_doc(doc_id, old, new)

        print(f"\n[READ] {doc_id} (after edit)")
        print(f"  {await read_doc(doc_id)}")

        print("\n[RESOURCE] docs://documents (JSON is parsed into a list)")
        print(f"  {await read_resource('docs://documents')}")

        print(f"\n[RESOURCE] docs://documents/{doc_id} (plain text)")
        print(f"  {await read_resource(f'docs://documents/{doc_id}')}")

        missing = "missing.md"
        print(f"\n[READ] {missing} (does not exist)")
        try:
            await read_doc(missing)
        except ToolError as e:
            print(f"ToolError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
