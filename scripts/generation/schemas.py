from pydantic import BaseModel
from typing import Literal, List
from langchain_core.documents import Document

class ChatRequest(BaseModel):
  src: str
  bsid: str | None = None
  contexts: List[Document] | None = None
  input: str | None = None
  model: str
  