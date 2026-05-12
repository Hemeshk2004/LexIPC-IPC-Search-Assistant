import os
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

# Load PDFs
pdf_loader = DirectoryLoader("data/", glob="*.pdf", loader_cls=PyPDFLoader)
docs = pdf_loader.load()

# Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(docs)

# ✅ Use latest HuggingFace embedding (free, no API key needed)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

vectordb = Chroma.from_documents(chunks, embedding=embeddings, persist_directory="db")
vectordb.persist()
print("✅ ChromaDB created successfully using HuggingFace embeddings!")
