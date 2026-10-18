import asyncio
import os

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

client = MultiServerMCPClient(
    {
        "tavily": {
            "transport": "streamable_http",
            "url": os.getenv("TAVILY_MCP_URL"),
        }
    }
)


async def get_tools():
    """Fetch Tavily MCP tools asynchronously."""
    return await client.get_tools()


def get_tools_sync():
    """Fetch Tavily MCP tools synchronously."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, client.get_tools()).result()

    return asyncio.run(client.get_tools())

