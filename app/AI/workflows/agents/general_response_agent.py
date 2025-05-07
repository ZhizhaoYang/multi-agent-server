from langgraph.prebuilt import create_react_agent

# from langchain_core.prompts import ResponseTemplate

from app.AI.core.llm import LLMFactory, LLMConfig

llm = LLMFactory.create_llm(
    LLMConfig(
        model="deepseek-chat",
        temperature=0.5,
    )
)

prompt = """Just directly response the user query via LLM"""

general_response_agent = create_react_agent(
    llm,
    tools=[],
    prompt=prompt,
)
