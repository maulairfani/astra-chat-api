import re
import json
import os
import firebase_admin
from firebase_admin import credentials, firestore
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import chromadb
from scripts.core import settings

class KnowledgeDB:
  def __init__(self):
    self.embeddings_func = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
    self.docs_limit = 10
    
    # Initialize Firebase if not already initialized
    if not firebase_admin._apps:
      cred = credentials.Certificate(json.loads(os.environ['FIREBASE_CREDENTIALS']))
      firebase_admin.initialize_app(cred)
    
    self.fsclient = firestore.client()

  def create_langchain_documents(self, file_path="data/parsed_pdf.json", metadata: dict | None = None):
    with open(file_path, 'r') as file:
      docs_dict = json.loads(file.read())

    docs = []
    ids = []

    for page, page_content in docs_dict.items():
      if len(docs) == self.docs_limit:
        break
      
      # Id
      ids.append(f"page-{page}")

      # Extract indicator
      matches = re.findall(r"\d+-\d+", page_content)

      disclosed = ""
      for m in matches:
        if m in settings.VALID_INDICATORS and m not in disclosed:
          disclosed += f";{m}"
        disclosed = disclosed[1:]
  
      # Metadata
      if metadata is not None:
        metadata["page"] = page
        metadata["disclosed"] = disclosed
      else:
        metadata = {"page": page, "disclosed": disclosed}

      docs.append(Document(
        page_content=page_content,
        metadata=metadata,
        id=f"page-{page}"
      ))
    return docs, ids

  def create_fs_documents(self, file_path="data/parsed_pdf.json"):
    with open(file_path, 'r') as file:
      docs_dict = json.loads(file.read())

    disclosure_doc = {}
    for idx, (page, page_content) in enumerate(docs_dict.items()):
      if idx == self.docs_limit:
        break
      
      # Extract indicator
      matches = re.findall(r"\d+-\d+", page_content)

      for m in matches:
        if m in settings.VALID_INDICATORS:
          if m not in disclosure_doc:
            disclosure_doc[m] = [f"page-{page}"]
          elif m in disclosure_doc and page not in disclosure_doc[m]:
            disclosure_doc[m].append(f"page-{page}")
    return disclosure_doc
          
  def create_knowledge_db(self):
    # Save to vector store
    docs, ids = self.create_langchain_documents()
    disclosure_doc = self.create_fs_documents()
    print(docs, ids)
    print(disclosure_doc)

    vector_store = Chroma(
      collection_name=settings.COLLECTION_NAME,
      persist_directory=settings.PERSIST_DIRECTORY,
      embedding_function=self.embeddings_func
    )
    ids = vector_store.add_documents(docs, ids=ids)
    print(ids)

    # Save to firestore
    pass

  def delete_knowledge_db(self):
    # Delete from vector store
    client = chromadb.PersistentClient(settings.PERSIST_DIRECTORY)
    client.reset()
    return "Deleted"
  