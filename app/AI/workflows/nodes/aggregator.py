from langgraph.types import Command
from langgraph.graph import END

from app.AI.workflows.models.chat_state import ChatWorkflowState, ChatNode, ChatNodeType
from app.AI.core.llm import LLMFactory, LLMConfig
from app.AI.workflows.constants import NodeNames

llm = LLMFactory.create_llm(
    LLMConfig(
        provider="deepseek",
        model="deepseek-chat",
        temperature=0.5,
    )
)

async def aggregator_node(state: ChatWorkflowState) -> Command:
    current_node = ChatNode(
        name=NodeNames.GENERAL_RESPONSE.value,
        type=ChatNodeType.WORKER,
    )

    # Ensure all contents are strings
    all_contents = [str(msg.content) for msg in state.messages if hasattr(msg, 'content') and isinstance(msg.content, str)]
    joined_content = "\n".join(all_contents)

    prompt = (
        "You are an expert AI assistant. "
        "Given the following information collected from multiple expert agents, "
        "please write a clear, concise, and user-friendly answer for the user. "
        "Do not simply concatenate the information, but synthesize it into a natural, helpful response.\n\n"
        f"Collected information:\n{joined_content}"
    )

    summary = await llm.ainvoke(prompt)
    summary_text = summary.content if hasattr(summary, 'content') and isinstance(summary.content, str) else str(summary)
    return Command(
        update={
            "current_output": summary_text,
            "next_steps": [current_node],
            "messages": [summary]
        },
        goto=END
    )