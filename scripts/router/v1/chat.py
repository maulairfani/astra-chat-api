from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from langchain_groq import ChatGroq
import os
from scripts.generation import ChatRequest
from scripts.retrieval import Retriever

router = APIRouter()

@router.post("/chat")
async def chat(request: Request, response: Response, chat_request: ChatRequest):
  # LLM
  llm = ChatGroq(model=chat_request.model, api_key=os.environ['GROQ_API_KEY'])
  
  # Step 1: Retrieval
  retriever = Retriever(llm)
  contexts = retriever.get_relevant_contents(chat_request)
  return contexts

