from typing import List
from llama_index.core import Document, VectorStoreIndex, Settings, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.faiss import FaissMapVectorStore
import faiss
from pathlib import Path
from transformers import AutoTokenizer

from config.logger_config import setup_logger
from src.core.exceptions import IndexingError
from config.config import RAGConfig

logger = setup_logger(__name__)

class IndexingService:

    def __init__(self, config: RAGConfig = RAGConfig()):
        self.config = config
        self._setup_models()
        logger.info("IndexingService initialized")

    def _setup_models(self):
        self.embed_model = HuggingFaceEmbedding(model_name=self.config.EMBEDDING_MODEL)
        self.text_splitter = SentenceSplitter(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP
        )
        Settings.embed_model = self.embed_model
        Settings.text_splitter = self.text_splitter

    def create_documents(self, content_list: List[str]) -> List[Document]:
        try:
            documents = [Document(text=content) for content in content_list]
            logger.info(f"Created {len(documents)} documents")
            return documents
        except Exception as e:
            logger.error(f"Error creating documents: {str(e)}")
            raise IndexingError(f"Failed to create documents: {str(e)}")
        
    def create_faiss_index(self, documents: List[Document]) -> VectorStoreIndex:
        try:
            logger.info(f"Creating FAISS index for {len(documents)} documents")
            
            faiss_index = faiss.IndexFlatL2(self.config.EMBEDDING_DIMENSION)
            id_map_index = faiss.IndexIDMap2(faiss_index)
            vector_store = FaissMapVectorStore(faiss_index=id_map_index)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)

            index = VectorStoreIndex.from_documents(
                documents=documents,
                storage_context=storage_context,
                transformations=[self.text_splitter],
                show_progress=True
            )
            
            logger.info("FAISS index created successfully")
            logger.info(f"Token count: {self.__count_tokens(documents)}")
            return index
            
        except Exception as e:
            logger.error(f"Error creating FAISS index: {str(e)}")
            raise IndexingError(f"Failed to create FAISS index: {str(e)}")
        
    def save_index(self, index: VectorStoreIndex, persist_dir: str) -> None:
        try:
            save_dir = persist_dir or self.config.INDEX_DIR
            Path(save_dir).mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Saving index to {save_dir}")
            index.storage_context.persist(persist_dir=save_dir)
            logger.info("Index saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
            raise IndexingError(f"Failed to save index: {str(e)}")
        
    def load_index(self, persist_dir: str):
        try:
            load_dir = persist_dir or self.config.INDEX_DIR
            
            if not Path(load_dir).exists():
                raise IndexingError(f"Index directory does not exist: {load_dir}")
            
            logger.info(f"Loading index from {load_dir}")
            
            vector_store = FaissMapVectorStore.from_persist_dir(load_dir)
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store, 
                persist_dir=load_dir
            )
            
            from llama_index.core import load_index_from_storage
            index = load_index_from_storage(
                storage_context=storage_context, 
                embed_model=self.embed_model
            )
            
            logger.info("Index loaded successfully")
            return index, vector_store, storage_context.docstore
            
        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")
            raise IndexingError(f"Failed to load index: {str(e)}")
        
    def __count_tokens(self, documents: List[Document]) -> int:
        tokenizer = AutoTokenizer.from_pretrained(self.config.EMBEDDING_MODEL)
        return sum(len(tokenizer.encode(doc.text, add_special_tokens=False)) for doc in documents)