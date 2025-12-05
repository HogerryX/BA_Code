from typing import List
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import NodeWithScore

from config.logger_config import setup_logger
from src.core.exceptions import RetrievalError
from config.config import RAGConfig

logger = setup_logger(__name__)

class RetrievalService:

    def __init__(self, config: RAGConfig = RAGConfig()):
        self.config = config
        logger.info("RetrievalService initialized")

    def retrieve_documents(self, index, query: str, top_k: int | None = None) -> List[NodeWithScore]:
        try:
            k = top_k or self.config.DEFAULT_TOP_K
            logger.info(f"Retrieving top-{k} documents for query: '{query[:50]}...'")
            
            retriever = VectorIndexRetriever(
                index=index,
                similarity_top_k=k,
                embed_model=index._embed_model
            )
            
            retrieved_docs = retriever.retrieve(f"query: {query}")
            
            logger.info(f"Retrieved {len(retrieved_docs)} documents")
            return retrieved_docs
        
        except Exception as e:
            logger.error(f"Error during retrieval: {str(e)}")
            raise RetrievalError(f"Failed to retrieve documents: {str(e)}")