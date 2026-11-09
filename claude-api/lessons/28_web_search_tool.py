"""Tool use: The web search tool.

Web search runs on Anthropic's servers, so there is no function to write and no
tool_result to send: one request returns the finished answer. The response
includes the searches made and citations pointing at the sources.
"""

from pathlib import Path

from anthropic import Anthropic
from anthropic.types import WebSearchTool20250305Param
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
client = Anthropic()
MODEL = "claude-sonnet-5-5"

WEB_SEARCH_TOOL: WebSearchTool20250305Param = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 3,  # cap the number of searches per request
    # "allowed_domains": ["python.org"],  # optionally restrict the sources
}

if __name__ == "__main__":
    message = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        tools=[WEB_SEARCH_TOOL],
        messages=[
            {"role": "user", "content": "What is the latest stable Python release?"}
        ],
    )
    for block in message.content:
        if block.type == "server_tool_use":
            print("search:", block.input)
        elif block.type == "text":
            print(block.text)
            for citation in block.citations or []:
                if citation.type == "web_search_result_location":
                    print(f"  [{citation.title}] {citation.url}")
