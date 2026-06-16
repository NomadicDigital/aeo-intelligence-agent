from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_anthropic import ChatAnthropic

load_dotenv()

llm = ChatAnthropic(model_name="claude-haiku-4-5-20251001")
response = llm.invoke("What is the meaning of life?")
print(response)