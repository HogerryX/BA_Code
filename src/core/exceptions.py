class RAGException(Exception):
    pass

class FileProcessingError(RAGException):
    pass

class IndexingError(RAGException):
    pass

class RetrievalError(RAGException):
    pass

class LLMError(RAGException):
    pass