from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from langchain_groq import ChatGroq
import os
from scripts.generation import ChatRequest
from scripts.retrieval import PDFParser, KnowledgeDatabase

router = APIRouter(prefix="/knowledges", tags=["Knowledge"])

@router.get("/create")
async def create(request: Request, response: Response):
  # pdf_parser = PDFParser()
  # pdf_parser.parse()

  knowledge_db = KnowledgeDatabase()
  knowledge_db.create_knowledge_database()

@router.get("/delete")
async def delete(request: Request, response: Response):
  # pdf_parser = PDFParser()
  # pdf_parser.parse()

  knowledge_db = KnowledgeDatabase()
  knowledge_db.delete_knowledge_database()

