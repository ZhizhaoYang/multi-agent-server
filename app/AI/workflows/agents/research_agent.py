from langgraph.prebuilt import create_react_agent
# from langchain_core.messages import SystemMessage, HumanMessage

from app.AI.workflows.tools.search_web_tool import search_web_tool
from app.AI.core.llm import LLMFactory, LLMConfig
# from langchain_core.prompts import ChatPromptTemplate

llm = LLMFactory.create_llm(
    LLMConfig(
        model="deepseek-chat",
        temperature=0.5,
    )
)

# prompt = """
#     User Question:
#     {input}

#     You are a researcher. Please use the tools provided to answer the user's question. DO NOT do any math.
# """

prompt = """
    User Question:
    {input}

    You are a weather agent. Please use the provided tools to answer the user's question about the weather.
"""


# prompt = ChatPromptTemplate.from_messages([
#     SystemMessage(
#         content=system_prompt),
#     HumanMessage(content="{input}"),
# ])

research_agent = create_react_agent(
    llm, tools=[search_web_tool], prompt=prompt,
)
