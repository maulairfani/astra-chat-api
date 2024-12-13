from pydantic import BaseModel
from typing import Literal, List

class ChatRequest(BaseModel):
  src: str
  bsid: str | None = None
  input: str | None = None
  model: str
  