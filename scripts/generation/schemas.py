from pydantic import BaseModel
from typing import Literal, List

class ChatItem(BaseModel):
  type: Literal["text"] = "text"
  content: str
  role: Literal["system", "user", "assistant"] | None = None

class ChatRequest(BaseModel):
  src: str
  bsid: str | None = None
  inputs: List[ChatItem]
  model: str
  