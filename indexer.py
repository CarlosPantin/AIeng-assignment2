import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
all_docs = []

articles_dir = "articles"

for filename in os.listdir(articles_dir):
    if filename.endswith(".pdf"):
        print(f"--- Indexing: {filename} ---")
        path = os.path.join(articles_dir, filename)
        
        loader = PyMuPDFLoader(path)
        data = loader.load()
        
        extracted_text = " ".join([p.page_content for p in data]).strip()
        if len(extracted_text) < 200:
            print(f"!!! ERROR: {filename} cannot be read.")
            continue
            
        chunks = text_splitter.split_documents(data)
        all_docs.extend(chunks)
        print(f"Done: {len(chunks)} chunks created.")

if all_docs:
    vectorstore = FAISS.from_documents(all_docs, embeddings)
    vectorstore.save_local("faiss_index")
    print("\nSUCCESS")
else:
    print("\nFATAL ERROR")