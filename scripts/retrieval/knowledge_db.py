import os
import json
import re
import shutil
import firebase_admin
from firebase_admin import credentials, firestore
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import chromadb
from scripts.core import settings

class KnowledgeDatabase:
  def __init__(self):
    self.embedding_function = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
    self.document_limit = 999
    self.firestore_path = "sustainabilityReports/ASII"

    self._initialize_firebase()
    self.firestore_client = firestore.client()

  def _initialize_firebase(self):
    "Initialize Firebase."
    if not firebase_admin._apps:
      firebase_credentials = os.environ.get('FIREBASE_CREDENTIALS')
      if not firebase_credentials:
        raise ValueError("Environment variable 'FIREBASE_CREDENTIALS' is not set.")
      credentials_data = json.loads(firebase_credentials)
      firebase_admin.initialize_app(credentials.Certificate(credentials_data))

  def _load_documents_from_file(self, file_path):
    "Load documents from a JSON file."
    if not os.path.exists(file_path):
      raise FileNotFoundError(f"The file {file_path} does not exist.")
    with open(file_path, 'r') as file:
      return json.load(file)

  def _extract_valid_indicators(self, content):
    "Extract valid indicators from content."
    matches = re.findall(r"\d+-\d+", content)
    return ";".join({match for match in matches if match in settings.VALID_INDICATORS})

  def create_documents(self, file_path="data/parsed_pdf.json", base_metadata=None):
    "Create LangChain Document objects."
    documents_data = self._load_documents_from_file(file_path)

    documents = []
    document_ids = []

    for page_number, page_content in list(documents_data.items())[:self.document_limit]:
      document_id = f"page-{page_number}"
      document_ids.append(document_id)

      disclosed_indicators = self._extract_valid_indicators(page_content)

      metadata = (base_metadata.copy() if base_metadata else {})
      metadata.update({"page": page_number, "disclosed": disclosed_indicators})

      documents.append(Document(
        page_content=page_content,
        metadata=metadata,
        id=document_id
      ))

    return documents, document_ids

  def create_disclosure_mapping(self, file_path="data/parsed_pdf.json"):
    "Create mapping of indicators to page IDs."
    documents_data = self._load_documents_from_file(file_path)
    disclosure_mapping = {}

    for index, (page_number, page_content) in enumerate(documents_data.items()):
      if index == self.document_limit:
        break

      matches = re.findall(r"\d+-\d+", page_content)
      valid_matches = [match for match in matches if match in settings.VALID_INDICATORS]

      for indicator in valid_matches:
        page_id = f"page-{page_number}"
        if indicator not in disclosure_mapping:
          disclosure_mapping[indicator] = [page_id]
        elif page_id not in disclosure_mapping[indicator]:
          disclosure_mapping[indicator].append(page_id)

    return disclosure_mapping

  def create_knowledge_database(self, file_path="data/parsed_pdf.json"):
    "Create knowledge database and save it."
    documents, document_ids = self.create_documents(file_path=file_path)
    disclosure_mapping = self.create_disclosure_mapping(file_path=file_path)

    vector_store = Chroma(
      collection_name=settings.COLLECTION_NAME,
      persist_directory=settings.PERSIST_DIRECTORY,
      embedding_function=self.embedding_function
    )
    for doc, id in zip(documents, document_ids):
      _ = vector_store.add_documents([doc], ids=[id])
      print(_)

    firestore_document = self.firestore_client.document(self.firestore_path)
    firestore_document.set({'disclosure': disclosure_mapping})

    return True

  def delete_knowledge_database(self):
    "Delete the knowledge database."
    client = chromadb.PersistentClient(settings.PERSIST_DIRECTORY)
    client.reset()

    if os.path.exists(settings.PERSIST_DIRECTORY):
      shutil.rmtree(settings.PERSIST_DIRECTORY)

    firestore_document = self.firestore_client.document(self.firestore_path)
    firestore_document.delete()

    return True
