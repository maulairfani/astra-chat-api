import os
import json
import re
import yaml
import firebase_admin
from firebase_admin import credentials, firestore
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from scripts.core import settings
from scripts.generation import ChatRequest

class Retriever:
  def __init__(self, llm: ChatGroq):
    self.llm = llm
    self.embedding_function = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
    self.vector_database = Chroma(
      settings.COLLECTION_NAME,
      self.embedding_function,
      persist_directory=settings.PERSIST_DIRECTORY
    )
    self.classification_prompt = self._load_prompt()
    self._initialize_firebase()
    self.firestore_client = firestore.client()
    self.report_disclosure_path = "sustainabilityReports/ASII"

  def _initialize_firebase(self):
    if not firebase_admin._apps:
      credentials_json = os.environ.get('FIREBASE_CREDENTIALS')
      if not credentials_json:
        raise ValueError("Environment variable 'FIREBASE_CREDENTIALS' is not set.")
      firebase_credentials = credentials.Certificate(json.loads(credentials_json))
      firebase_admin.initialize_app(firebase_credentials)

  def fetch_relevant_documents(self, query_request: ChatRequest):
    retrieved_contexts = []
    retrieved_contexts.extend(self.retrieve_using_language_model(query_request.input))
    # retrieved_contexts.extend(self.retrieve_using_embeddings(query_request.input))
    return retrieved_contexts

  def retrieve_using_embeddings(self, query, top_k=4):
    return self.vector_database.similarity_search(query, k=top_k)

  def retrieve_using_language_model(self, query):
    formatted_prompt = self.classification_prompt.format(question=query)
    llm_response = self.llm.invoke(formatted_prompt)
    indicator_pattern = r"\d+-\d+\b"
    matched_indicators = re.findall(indicator_pattern, llm_response.content)

    relevant_indicators = [indicator for indicator in matched_indicators if indicator in settings.VALID_INDICATORS]#[:1] # Limit to 1
    print(relevant_indicators)

    document_snapshot = self.firestore_client.document(self.report_disclosure_path).get()
    disclosure_data = document_snapshot.to_dict().get('disclosure', {})
    related_page_ids = set()
    for indicator in relevant_indicators:
        related_page_ids.update(disclosure_data.get(indicator, []))
    related_page_ids = list(related_page_ids)
    

    document_contexts = self.vector_database.get(ids=related_page_ids, include=["documents", "metadatas"])
    return [
      Document(page_content=content, metadata=metadata, id=document_id)
      for document_id, content, metadata in zip(document_contexts["ids"], document_contexts["documents"], document_contexts["metadatas"])
    ]

  def _load_prompt(self):
    with open('scripts/retrieval/cls_prompt.yml', 'r') as file:
      prompt_data = yaml.safe_load(file)
    return prompt_data['cls_prompt']
