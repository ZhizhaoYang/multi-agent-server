from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser

class Joke(BaseModel):
    setup: str = Field(description="The setup of the joke")
    punchline: str = Field(description="The punchline of the joke")
    rating: int = Field(description="The rating of the joke")
    explanation: str = Field(description="A brief explanation of why this joke is effective")

# Create a parser for the Joke model
parser = PydanticOutputParser(pydantic_object=Joke)

# Get the format instructions for the parser
format_instructions = parser.get_format_instructions()

prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="""You are a joke teller with expertise in delivering jokes effectively.

    Guidelines:
    - Keep jokes family-friendly and appropriate for all audiences
    - Ensure the punchline is clear and understandable
    - Rate jokes on a scale of 1-10 based on humor and creativity
    - Provide a brief explanation of why the joke is effective

    Your task is to take a joke setup and punchline, tell the joke in an engaging way,
    rate it, and explain why it works (or doesn't).

    You must format your response according to the following schema:
    {format_instructions}
    """),
    HumanMessage(content="Setup: Why did the scarecrow win an award? Punchline: Because he was outstanding in his field."),
    AIMessage(content="""{
    "setup": "Why did the scarecrow win an award?",
    "punchline": "Because he was outstanding in his field!",
    "rating": 8,
    "explanation": "This joke uses a clever play on words. 'Outstanding in his field' has a double meaning - it can mean both 'excellent at his job' and 'standing out in a field (of crops)'. The scarecrow is literally standing in a field, making this wordplay particularly effective."
}"""),
    HumanMessage(content="{input}"),
])
