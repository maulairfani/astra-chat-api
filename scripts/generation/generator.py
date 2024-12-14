from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
import os
from typing import List
import yaml

from scripts.generation import ChatRequest

class Generator:
  def __init__(self, model_name):
    self.llm = ChatGroq(model=model_name, api_key=os.environ['GROQ_API_KEY'])

  def generate_response(self, item: ChatRequest):
    messages = self._build_prompt(item.contexts, item.input)
    response = self.llm.invoke(messages)
    return response.content

  def _build_prompt(self, contexts, question):
    with open('scripts/generation/rag_prompt.yml', 'r') as file:
      prompt_data = yaml.safe_load(file)
      prompt = prompt_data['rag_prompt']

    formatted_prompt = prompt.format(contexts=contexts)
    messages = [
      SystemMessage(content=formatted_prompt),
      HumanMessage(content=question)
    ]
    return messages