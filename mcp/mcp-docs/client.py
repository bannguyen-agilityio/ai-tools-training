import asyncio

from fastmcp import Client

client = Client("server.py")


async def main():
    # One session for everything, so edits persist between calls.
    async with client:
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")


if __name__ == "__main__":
    asyncio.run(main())
