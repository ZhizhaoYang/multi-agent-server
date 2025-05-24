from langchain_core.runnables import Runnable
from typing import Any

async def stream_generator(graph: Runnable, inputs: Any, stream_mode: str = "messages"):
    async for chunk in graph.astream(inputs, stream_mode=stream_mode):
        yield chunk