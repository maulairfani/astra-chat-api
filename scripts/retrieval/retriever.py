import yaml
from langchain_groq import ChatGroq
import re
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from langchain_core.documents import Document
from scripts.core import settings
from scripts.generation import ChatRequest

class Retriever:
  def __init__(self, llm: ChatGroq):
    self.llm = llm
    self.embedding_func = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
    self.vector_store = Chroma(settings.COLLECTION_NAME, self.embedding_func, persist_directory=settings.PERSIST_DIRECTORY)
    self.cls_prompt = self._load_prompt()
    self._initialize_firebase()
    self.fsclient = firestore.client()
    self.disclosure_path = "sustainabilityReports/ASII"

  def _initialize_firebase(self):
    """Initialize Firebase if not already initialized."""
    if not firebase_admin._apps:
      firebase_credentials_str = os.environ['FIREBASE_CREDENTIALS']
      if not firebase_credentials_str:
        raise ValueError("FIREBASE_CREDENTIALS environment variable is not set.")
      cred_dict = json.loads(firebase_credentials_str)
      cred = credentials.Certificate(cred_dict)
      firebase_admin.initialize_app(cred)

  def get_relevant_contents(self, item: ChatRequest):
    contexts = []

    # From LLM
    contexts.extend(self.llm_based_retrieval(item.input))

    # From Vector Store
    contexts.extend(self.embeddings_based_retrieval(item.input))
    
    return contexts
    
  def embeddings_based_retrieval(self, query, k=4):
    contexts = self.vector_store.similarity_search(query, k=k)
    return contexts

  def llm_based_retrieval(self, query):
    # Indicator classification
    formatted_prompt = self.cls_prompt.format(question=query)
    response = self.llm.invoke(formatted_prompt)

    # Extract indicator from response
    pattern = r"\d+-\d+\b"
    matches = re.findall(pattern, response.content)
    
    # Validation
    related_indicator = []
    for m in matches:
      if m in settings.VALID_INDICATORS and m not in related_indicator:
        related_indicator.append(m)

    # TEMPORARY
    related_indicator = ['2-22']
    
    page_ids = []
    doc_ref = self.fsclient.document(self.disclosure_path)
    doc_snap = doc_ref.get()
    disclosure_doc = doc_snap.to_dict().get('disclosure', [])
    for indicator in related_indicator:
      # Get page ids
      page_ids.extend(disclosure_doc.get(indicator))

    # Get contexts
    contexts_dict = self.vector_store.get(ids=page_ids, include=["documents", "metadatas"])

    contexts_list = []
    for page_id, page_content, metadata in zip(contexts_dict["ids"], contexts_dict["documents"], contexts_dict["metadatas"]):
      contexts_list.append(Document(
        page_content=page_content,
        metadata=metadata,
        id=page_id
      ))
    
    return contexts_list

  def _load_prompt(self):
    with open('scripts/retrieval/cls_prompt.yml', 'r') as file:
      prompt = yaml.safe_load(file)

    return prompt['cls_prompt']
