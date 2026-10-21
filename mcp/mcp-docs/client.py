import asyncio

from fastmcp import Client
from mcp.types import TextContent

client = Client("server.py")


async def read_doc(doc_id: str) -> str:
    result = await client.call_tool("read_doc_contents", {"doc_id": doc_id})
    content = result.content[0]
    assert isinstance(content, TextContent)
    return content.text


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


if __name__ == "__main__":
    asyncio.run(main())
