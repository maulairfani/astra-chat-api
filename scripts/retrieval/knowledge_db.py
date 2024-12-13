import os
import json
import re

import firebase_admin
from firebase_admin import credentials, firestore

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import chromadb
import shutil

from scripts.core import settings


class KnowledgeDB:
  def __init__(self):
    self.embeddings_func = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
    self.docs_limit = 10
    self.disclosure_path = "sustainabilityReports/ASII"

    self._initialize_firebase()
    self.fsclient = firestore.client()

  def _initialize_firebase(self):
    """Initialize Firebase if not already initialized."""
    if not firebase_admin._apps:
      firebase_credentials_str = os.environ['FIREBASE_CREDENTIALS']
      if not firebase_credentials_str:
        raise ValueError("FIREBASE_CREDENTIALS environment variable is not set.")
      cred_dict = json.loads(firebase_credentials_str)
      cred = credentials.Certificate(cred_dict)
      firebase_admin.initialize_app(cred)

  def _load_docs_from_json(self, file_path: str) -> dict:
    """Load and return the document data from a JSON file."""
    if not os.path.exists(file_path):
      raise FileNotFoundError(f"The file {file_path} does not exist.")

    with open(file_path, 'r') as file:
      docs_dict = json.load(file)
    return docs_dict

  def _extract_disclosed_indicators(self, page_content: str) -> str:
    """
    Extract all valid indicators from page_content.
    Returns a string of disclosed indicators separated by semicolons.
    """
    matches = re.findall(r"\d+-\d+", page_content)
    disclosed_set = {m for m in matches if m in settings.VALID_INDICATORS}
    return ";".join(disclosed_set)

  def create_langchain_documents(self, file_path: str = "data/parsed_pdf.json", base_metadata: dict | None = None):
    """
    Creates LangChain Document objects along with their IDs from a given JSON file.

    :param file_path: Path to the parsed PDF JSON file.
    :param base_metadata: Optional base metadata to be included in each document.
    :return: A tuple of (documents_list, ids_list).
    """
    docs_dict = self._load_docs_from_json(file_path)

    documents = []
    ids = []

    for page, page_content in list(docs_dict.items())[:self.docs_limit]:
      doc_id = f"page-{page}"
      ids.append(doc_id)

      disclosed = self._extract_disclosed_indicators(page_content)

      # Merge the base metadata with page-specific metadata
      metadata = (base_metadata.copy() if base_metadata else {})
      metadata.update({"page": page, "disclosed": disclosed})

      documents.append(Document(
        page_content=page_content,
        metadata=metadata,
        id=doc_id
      ))

    return documents, ids

  def create_disclosure_mapping(self, file_path: str = "data/parsed_pdf.json") -> dict:
    """
    Creates a mapping of indicator -> list of page IDs from the JSON file.

    :param file_path: Path to the parsed PDF JSON file.
    :return: Dictionary where keys are indicators and values are lists of page IDs.
    """
    docs_dict = self._load_docs_from_json(file_path)
    disclosure_doc = {}

    for idx, (page, page_content) in enumerate(docs_dict.items()):
      if idx == self.docs_limit:
        break

      matches = re.findall(r"\d+-\d+", page_content)
      valid_matches = [m for m in matches if m in settings.VALID_INDICATORS]

      for indicator in valid_matches:
        page_id = f"page-{page}"
        if indicator not in disclosure_doc:
          disclosure_doc[indicator] = [page_id]
        elif page_id not in disclosure_doc[indicator]:
          disclosure_doc[indicator].append(page_id)

    return disclosure_doc

  def create_knowledge_db(self, file_path: str = "data/parsed_pdf.json"):
    """
    Creates a knowledge database by:
    1. Extracting documents and creating a vector store.
    2. Saving disclosure mappings to Firestore.

    :param file_path: Path to the parsed PDF JSON file.
    :return: True if successful.
    """
    # Create documents for vector store
    documents, ids = self.create_langchain_documents(file_path=file_path)

    # Create a disclosure mapping for Firestore
    disclosure_doc = self.create_disclosure_mapping(file_path=file_path)

    # Save to vector store
    vector_store = Chroma(
      collection_name=settings.COLLECTION_NAME,
      persist_directory=settings.PERSIST_DIRECTORY,
      embedding_function=self.embeddings_func
    )
    vector_store.add_documents(documents, ids=ids)

    # Save disclosure mapping to Firestore
    doc_ref = self.fsclient.document(self.disclosure_path)
    doc_ref.set({'disclosure': disclosure_doc})

    return True

  def delete_knowledge_db(self):
    """
    Deletes the knowledge database by:
    1. Resetting the local vector store.
    2. Deleting the disclosure document from Firestore.
    3. Removing the persisted directory.

    :return: True if successful.
    """

    # Delete from vector store
    client = chromadb.PersistentClient(settings.PERSIST_DIRECTORY)
    client.reset()

    # Remove the persisted directory
    if os.path.exists(settings.PERSIST_DIRECTORY):
        shutil.rmtree(settings.PERSIST_DIRECTORY)

    # Delete from Firestore
    doc_ref = self.fsclient.document(self.disclosure_path)
    doc_ref.delete()

    return True
