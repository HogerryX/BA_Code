from typing import List, Dict, Any, TypedDict
from pathlib import Path
from llama_index.core.schema import NodeWithScore

from config.logger_config import setup_logger
from config.config import RAGConfig
from src.core.exceptions import RAGException
from src.services.file_handler import FileHandler
from src.services.document_processor import DocumentProcessor
from src.services.indexing_service import IndexingService
from src.services.retrieval_service import RetrievalService
from src.services.llm_service import LLMService

logger = setup_logger(__name__)

class ChatbotResponse(TypedDict):
    documents: List[NodeWithScore]
    answer: str | None

class RAGSystem:
    
    def __init__(self, config: RAGConfig | None = None):
        self.config = config or RAGConfig()
        
        self.file_handler = FileHandler(self.config)
        self.document_processor = DocumentProcessor(self.config)
        self.indexing_service = IndexingService(self.config)
        self.retrieval_service = RetrievalService(self.config)
        self.llm_service = LLMService(self.config)
        
        self._index = None
        self._vector_store = None
        self._docstore = None
        
        logger.info("RAG System initialized successfully")
    
    def initialize_system(self, data_path: str | None = None, force_rebuild: bool = False) -> None:
        try:
            index_exists = Path(self.config.INDEX_DIR).exists()
            
            if not index_exists or force_rebuild:
                logger.info("Building new index...")
                self._build_index(data_path or self.config.DATA_DIR)
            
            logger.info("Loading index...")
            self._load_index()
            
            logger.info("RAG System ready for queries")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {str(e)}")
            raise RAGException(f"System initialization failed: {str(e)}")
    
    def chatbot_endpoint(self, query: str, model: str | None, conversation_history: List[Dict] | None = None, top_k: int | None = None) -> ChatbotResponse:
        try:
            logger.info(f"Chatbot query received: '{query[:50]}...'")
            
            if not self._index:
                raise RAGException("System not initialized. Call initialize_system() first.")
            
            documents = self.retrieval_service.retrieve_documents(self._index, query, top_k)
            
            answer = self.llm_service.generate_chatbot_response(query, documents, model, conversation_history)

            response = ChatbotResponse(documents=documents, answer=answer)

            logger.info("Chatbot response generated successfully")
            return response
            
        except Exception as e:
            logger.error(f"Chatbot endpoint error: {str(e)}")
            raise RAGException(f"Chatbot query failed: {str(e)}")
    
    def quiz_endpoint(self, interests: str, model: str | None, num_questions: int = 5, top_k: int | None = None) -> str | None:
        try:
            logger.info(f"Quiz generation requested for interests: '{interests[:50]}...'")
            
            if not self._index:
                raise RAGException("System not initialized. Call initialize_system() first.")
            
            retrieval_query = self._generate_retrieval_query(interests)
            
            documents = self.retrieval_service.retrieve_documents(self._index, retrieval_query, top_k)
            
            quiz_json = self.llm_service.generate_quiz_questions(documents, model, num_questions)
            
            logger.info("Quiz questions generated successfully")
            return quiz_json
            
        except Exception as e:
            logger.error(f"Quiz endpoint error: {str(e)}")
            raise RAGException(f"Quiz generation failed: {str(e)}")
    
    def character_endpoint(self, query: str, model: str | None, character: str = "faust", temperature: float = 0.9) -> str | None:
        try:
            logger.info(f"Character conversation with {character}: '{query[:50]}...'")
            
            response = self.llm_service.generate_character_response(query, model, character, temperature)
            
            logger.info(f"{character} response generated successfully")
            return response
            
        except Exception as e:
            logger.error(f"Character endpoint error: {str(e)}")
            raise RAGException(f"Character conversation failed: {str(e)}")
    
    def _build_index(self, data_path: str) -> None:
        logger.info(f"Building index from {data_path}")
        
        all_files = self.file_handler.get_files_recursive(data_path)
        
        supported_files = self.file_handler.filter_supported_files(all_files)
        
        content_list = []
        total_files = sum(len(files) for files in supported_files.values())
        processed_count = 0
        
        for ext, files in supported_files.items():
            for file_path in files:
                try:
                    if ext == '.pdf':
                        content = self.document_processor.process_pdf(file_path)
                    elif ext == '.docx':
                        content = self.document_processor.process_docx(file_path)
                    else:
                        continue
                    
                    content_list.append(content)
                    processed_count += 1
                    logger.info(f"Processed {processed_count}/{total_files}: {file_path}")
                    
                except Exception as e:
                    logger.warning(f"Failed to process {file_path}: {str(e)}")
                    continue
        
        if not content_list:
            raise RAGException("No documents were successfully processed")
        
        documents = self.indexing_service.create_documents(content_list)
        index = self.indexing_service.create_faiss_index(documents)
        
        self.indexing_service.save_index(index, './data/Index')
        
        logger.info(f"Index built successfully with {len(documents)} documents")
    
    def _load_index(self) -> None:
        self._index, self._vector_store, self._docstore = self.indexing_service.load_index('./data/Index')
        logger.info("Index loaded successfully")
    
    def _generate_retrieval_query(self, interests: str) -> str:

        return interests
    
    def get_system_status(self) -> Dict[str, Any]:
        return {
            "initialized": self._index is not None,
            "config": {
                "model": self.config.DEFAULT_MODEL,
                "embedding_model": self.config.EMBEDDING_MODEL,
                "chunk_size": self.config.CHUNK_SIZE,
                "default_top_k": self.config.DEFAULT_TOP_K
            },
            "index_info": {
                "exists": Path(self.config.INDEX_DIR).exists(),
                "path": self.config.INDEX_DIR
            }
        }