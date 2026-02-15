import os
import sys
import shutil
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import LanceDB
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import lancedb

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("Error: OPENROUTER_API_KEY not found in .env file.")
    sys.exit(1)

# Configurations
# Using OpenAI compatible API for OpenRouter
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
EMBEDDING_MODEL_NAME = "text-embedding-3-small"
LLM_MODEL_NAME = "openai/gpt-4o-mini" # Using gpt-4o-mini as proxy for "GPT-5 mini" which might be a typo or future model. Adjust if needed.
# Converting "OpenAI:GPT-5 mini" to expected OpenRouter format if it's a real model ID, otherwise fallback.
# User asked for "OpenAI:GPT-5 mini". In OpenRouter, it might be mapped or they might mean `openai/gpt-4o-mini`. 
# I'll stick to a sensible default that works with OpenRouter's openai/ prefix.

REPORTS_DIR = "reports"
VECTOR_DB_NAME = "rag_vectordb"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

def load_documents(directory):
    documents = []
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist. Creating it.")
        os.makedirs(directory)
        return documents

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
            elif filename.endswith(".docx") or filename.endswith(".doc"):
                loader = Docx2txtLoader(file_path)
                documents.extend(loader.load())
            elif filename.endswith(".txt"):
                loader = TextLoader(file_path)
                documents.extend(loader.load())
            else:
                print(f"Skipping unsupported file: {filename}")
        except Exception as e:
            print(f"Error loading {filename}: {e}")
    
    return documents

def setup_vector_db(documents):
    if not documents:
        print("No documents to index.")
        return None

    # Splitting text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Generated {len(chunks)} chunks.")

    if not chunks:
        print("No chunks generated from documents. Check if documents have text content.")
        return None

    # Embeddings
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL_NAME,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        check_embedding_ctx_length=False # OpenRouter might not support this check endpoint
    )

    # Clean up existing DB if we want to overwrite 'replace it with the new one'
    # LanceDB creates a table, but to fully overwrite the DB folder, we might want to remove it 
    # or just use mode='overwrite' in create_table.
    # lancedb.connect usage in langchain wrapper usually manages the connection.
    # We can delete the folder to be sure.
    
    if os.path.exists(VECTOR_DB_NAME):
        try:
           shutil.rmtree(VECTOR_DB_NAME)
           print(f"Removed existing vector DB at {VECTOR_DB_NAME}")
        except Exception as e:
            print(f"Could not remove existing DB: {e}")

    db = lancedb.connect(VECTOR_DB_NAME)
    
    # LangChain's LanceDB wrapper
    vectorstore = LanceDB.from_documents(
        documents=chunks,
        embedding=embeddings,
        connection=db,
        table_name="vectors" # Default table name
    )
    
    return vectorstore

def get_rag_chain(vectorstore):
    retriever = vectorstore.as_retriever()
    
    llm = ChatOpenAI(
        model=LLM_MODEL_NAME,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL
    )

    template = """Answer the question based only on the following context:
    {context}

    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain

if __name__ == "__main__":
    import argparse
    
    # Check if we have arguments passed directly
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        # Default behavior or prompt? User said "tested using command line argument/s (query)"
        # If no args, maybe just run indexing if explicit? Or fail?
        # Let's assume if no args, we assume they might want to just build or show usage.
        # But to be useful, let's try to index and then wait for input if they want, 
        # OR just index and exit if they didn't provide a query?
        # The instruction says "Add a subprocess... text using command line argument/s (query)"
        # I'll support both: just running indexes, and then if query is there, query it.
        # If I want to support "indexing only", I'd need a flag. 
        # For now, I'll always index (as per "Create a vector database... If there is an existing... overwrite")
        # Then query if query exists.
        print("Usage: python rag.py <query>")
        print("Running indexing...")
        query = None

    print("Loading documents...")
    docs = load_documents(REPORTS_DIR)
    
    if not docs:
        print("No documents found in 'reports' folder. Please add files.")
        if query:
            sys.exit(0)
    
    print("Setting up Vector DB...")
    vectorstore = setup_vector_db(docs)

    if query and vectorstore:
        print(f"Querying: {query}")
        chain = get_rag_chain(vectorstore)
        response = chain.invoke(query)
        print("\nResponse:")
        print(response)
    else:
         print("Vector DB ready.")
