import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

def get_llm() -> ChatOpenAI:
  """
  Returns a configured ChatOpenAI instance using environment variables.
  """
  return ChatOpenAI(
    model=os.getenv("LLM_MODEL", "gpt-4.1-2025-04-14"),
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
  )

def get_default_prompt(system_message: str, human_message: str) -> ChatPromptTemplate:
  """
  Returns a ChatPromptTemplate with the given system and human messages.
  """
  return ChatPromptTemplate.from_messages([
    ("system", system_message),
    ("human", human_message)
  ]) 