from dataclasses import dataclass, field
from typing import List

@dataclass
class RAGConfig:

    DEFAULT_MODEL: str = "qwen3:1.7b"
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-small"
    EMBEDDING_DIMENSION: int = 384

    CHUNK_SIZE: int = 300
    CHUNK_OVERLAP: int = 30
    DEFAULT_TOP_K: int = 10

    SUPPORTED_EXTENSIONS: List[str] = field(default_factory=lambda: ['.pdf', '.docx'])
    INDEX_DIR: str = "./data/Index"
    DATA_DIR: str = "./data/files"

    PDF_CATEGORIES: List[str] = field(default_factory=lambda: ["Title", "NarrativeText"])
    LANGUAGE: str = "de"

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"