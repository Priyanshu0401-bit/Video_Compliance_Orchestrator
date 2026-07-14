import os
import glob
import logging
from dotenv import load_dotenv
load_dotenv(override=True)

#loaders and splitters
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

#azure components
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch

#setup logging
logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("indexer")

def index_docs():
    '''
    Reads the PDFs, chunks them, and upload them to Azure AI Search
    '''

    #define paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.join(current_dir,"../../backend/data")

    #check env variables
    logger.info("="*60)
    logger.info("Environment Configuration Check")
    logger.info(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    logger.info(f"AZURE_OPENAI_API_VERSION: {os.getenv('AZURE_OPENAI_API_VERSION')}")
    logger.info(f"Embedding Deployment: {os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT','text-embedding-3-small')}")
    logger.info(f"AZURE_SEARCH_ENDPOINT: {os.getenv('AZURE_SEARCH_ENDPOINT')}")
    logger.info(f"AZURE_SEARCH_INDEX_NAME: {os.getenv('AZURE_SEARCH_INDEX_NAME')}")
    logger.info("="*60)

    #validate env variables
    required_vars=[
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_API_KEY",
        "AZURE_SEARCH_INDEX_NAME",
        "AZURE_OPENAI_API_KEY"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("PLease check your .env file and ensure all the variables are set")
        return
    
    #initialize embedding model
    try:
        logger.info("Initializing Azure OpenAI Embeddings.....")
        embeddings = AzureOpenAIEmbeddings(
            azure_deployment = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT'),
            azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_key = os.getenv('AZURE_OPENAI_API_KEY'),
            api_version = os.getenv('AZURE_OPENAI_API_VERSION')
        )

        logger.info("Embedding model initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Azure OpenAI Embeddings: {e}")
        logger.error("Please verify you azure openai deployment name and endpoint.")
        return

    #Initialize Azure ai search
    try:
        logger.info("Initializing Azure AI Search Vector Store.....")
        vector_store = AzureSearch(
            azure_search_endpoint = os.getenv('AZURE_SEARCH_ENDPOINT'),
            azure_search_key = os.getenv('AZURE_SEARCH_API_KEY'),
            index_name = index_name,
            embedding_function = embeddings.embed_query,
        )

        logger.info("Vector store initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Azure AI Search: {e}")
        logger.error("Please verify your Azure Search endpoint and API key and index name")
        return

    #find pdf files
    pdf_files = glob.glob(os.path.join(data_folder,"*.pdf"))

    if not pdf_files:
        logger.warning(f"No PDF files found in the directory: {data_folder}")
        logger.warning("Please place your PDF files in the data folder")
        return
    
    logger.info(f"Found {len(pdf_files)} PDF files to process: {[os.path.basename(f) for f in pdf_files]}")

    all_splits = []

    for pdf_path in pdf_files:
        try:
            logger.info(f"Loading:{os.path.basename(pdf_path)}......")
            loader = PyPDFLoader(pdf_path)
            raw_docs = loader.load()

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size = 1000,
                chunk_overlap = 200,
            )
            splits = text_splitter.split_documents(raw_docs)
            for split in splits:
                split.metadata["source"] = os.path.basename(pdf_path)

            all_splits.extend(splits)
            logger.info(f"Split into {len(splits)} chunks.")

        except Exception as e:
            logger.error(f"Failed to load {pdf_path}: {e}")
            continue

        #upload to azure
        if all_splits:
            logger.info(f"Uploading {len(all_splits)} chunks to Azure AI Search...")
            try:
                #azure search accepts batches automaticall via this method
                vector_store.add_documents(documents=all_splits)
                logger.info("="*60)
                logger.info("Indexing complete")
                logger.info(f"Total chunks indexed : {len(all_splits)}")
                logger.info("="*60)

            except Exception as e:
                logger.error(f"Failed to upload to azure ai search: {e}")
                logger.error("Please verify your azure search endpoint and API key and index name")
            
        else:
            logger.warning("No documents were processed")

if __name__ == "__main__":
    index_docs()
                
            
            