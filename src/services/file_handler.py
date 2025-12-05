from pathlib import Path
from typing import List, Dict

from config.logger_config import setup_logger
from src.core.exceptions import FileProcessingError
from config.config import RAGConfig

logger = setup_logger(__name__)

class FileHandler:

    def __init__(self, config: RAGConfig = RAGConfig()):
        self.config = config
        logger.info("FileHandler initialized")

    def get_files_recursive(self, path: str) -> List[str]:
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                raise FileProcessingError(f"Directory does not exist: {path}")
            if not path_obj.is_dir():
                raise FileProcessingError(f"Path is not a directory: {path}")
            
            files = [] 
            for file_path in path_obj.rglob('*'):
                if file_path.is_file():
                    files.append(str(file_path))
                
            logger.info(f"Found {len(files)} files in {path}")
            return files
        
        except Exception as e:
            logger.error(f"Error scanning directory {path}: {str(e)}")
            raise FileProcessingError(f"Failed to scan directory: {str(e)}")
        
    def filter_supported_files(self, files: List[str]) -> Dict[str, List[str]]:
        supported_files = {ext: [] for ext in self.config.SUPPORTED_EXTENSIONS}
        unsupported_count = 0

        for file_path in files:
            file_extension = Path(file_path).suffix.lower()

            if file_extension in self.config.SUPPORTED_EXTENSIONS:
                if file_extension == '.docx' and 'englisch' in Path(file_path).name.lower():
                    unsupported_count += 1
                    continue
                supported_files[file_extension].append(file_path)
            else:
                unsupported_count += 1

        total_supported = sum(len(files) for files in supported_files.values())
        logger.info(f"Filtered files: {total_supported} supported, {unsupported_count} unsupported")

        return supported_files

