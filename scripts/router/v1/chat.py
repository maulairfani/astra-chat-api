from fastapi import APIRouter, Request, Response
from langchain_groq import ChatGroq
import os
from scripts.generation import ChatRequest, Generator
from scripts.retrieval import Retriever

router = APIRouter()

@router.post("/chat")
async def chat(request: Request, response: Response, item: ChatRequest):
  # LLM
  llm = ChatGroq(model=item.model, api_key=os.environ['GROQ_API_KEY'])
  
  # Step 1: Retrieval
  retriever = Retriever(llm)
  item.contexts = retriever.fetch_relevant_documents(item)

  # Step 2: Generation
  generator = Generator(item.model)
  ai_response = generator.generate_response(item)
  return ai_response
  

