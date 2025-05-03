from langchain_deepseek import ChatDeepSeek
from dotenv import load_dotenv, find_dotenv
import os
from pydantic import SecretStr
from langchain_mcp_adapters.client import MultiServerMCPClient, SSEConnection
from langgraph.prebuilt import create_react_agent
import asyncio

load_dotenv(find_dotenv())

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GAODE_SSE_URL = "https://mcp.amap.com/sse?key=26407dff266882483887a1095bdfb2bc"

model = ChatDeepSeek(
    model="deepseek-chat",
    api_key=SecretStr(DEEPSEEK_API_KEY) if DEEPSEEK_API_KEY else None,
)

config_gaode: SSEConnection = {
    "url": GAODE_SSE_URL,
    "transport": "sse",
    "headers": {},
    "timeout": 10,
    "sse_read_timeout": 10,
    "session_kwargs": {},
}


async def main():
    async with MultiServerMCPClient(
        {
            "gaode_map": config_gaode
        }
    ) as client:
        agent = create_react_agent(model, client.get_tools())

        # Set up the query
        query = "what is the longitude for Chengdu?"
        print(f"Question: {query}")
        print("Streaming response:")

        # response = await agent.ainvoke({"messages": "what is the longitude for Chengdu?"})
        # print(response["messages"][-1].content)

        # # Stream the response incrementally
        result = ""
        async for chunk in agent.astream({"messages": f"{query}"}):
            print(chunk)
            if "agent" in chunk:
                result = chunk["agent"]["messages"][-1].content
            # if "messages" in chunk and chunk["messages"]:
            #     current_content = chunk["messages"][-1].content
            #     # Only print the new content
            #     new_content = current_content[len(previous_content):]
            #     if new_content:
            #         # print("------- new_content ----------- \n")
            #         # print(new_content, end="", flush=True)
            #         previous_content = current_content


if __name__ == "__main__":
    asyncio.run(main())
