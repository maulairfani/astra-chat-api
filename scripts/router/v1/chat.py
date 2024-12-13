from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from scripts.generation import ChatRequest
from scripts.retrieval import Retriever

router = APIRouter()

@router.post("/chat")
async def chat(request: Request, response: Response, chat_request: ChatRequest):
  # Step 1: Retrieval
  retriever = Retriever()
  contexts = retriever.get_relevant_contents()

  # Step 2: Generation
  chunk = "Hello, world!"
  if chunk:
    return StreamingResponse(chunk, status_code=200, media_type="text/event-stream")


