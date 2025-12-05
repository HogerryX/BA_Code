from typing import List, Dict
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.docx import partition_docx
from langdetect import detect

from config.logger_config import setup_logger
from src.core.exceptions import FileProcessingError
from config.config import RAGConfig

logger = setup_logger(__name__)

class DocumentProcessor:

    def __init__(self, config: RAGConfig = RAGConfig()):
        self.config = config
        logger.info("DocumentProcessor initialized")

    def process_pdf(self, file_path: str) -> str:
        try:
            logger.info(f"Processing PDF: {file_path}")
            elements = partition_pdf(filename=file_path, strategy="auto")

            filtered_elements = self._filter_elements(elements, self.config.PDF_CATEGORIES)
            language_filtered = self._filter_by_language(filtered_elements, self.config.LANGUAGE)

            content = self._extract_content(language_filtered)
            markdown = self._create_markdown(content)

            logger.info(f"Sucessfully processed PDF: {file_path}")
            return markdown
        
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {str(e)}")
            raise FileProcessingError(f"Failed to process PDF: {str(e)}")
        
    def process_docx(self, file_path: str) -> str:
        try:
            logger.info(f"Processing DOCX: {file_path}")
            elements = partition_docx(file_path)

            language_filtered = self._filter_by_language(elements, self.config.LANGUAGE)

            content = self._extract_content(language_filtered)
            markdown = self._create_markdown(content)

            logger.info(f"Successfully processed DOCX: {file_path}")
            return markdown

        except Exception as e:
            logger.error(f"Error processing DOCX: {file_path}")
            raise FileProcessingError(f"Failed to process DOCX: {str(e)}")
        
    def _filter_elements(self, elements: List, categories: List[str]) -> List:
        return [el for el in elements if el.category in categories]
    
    def _filter_by_language(self, elements: List, target_language: str) -> List:
        filtered_elements = []

        for element in elements:
            try:
                detected_lang = detect(element.text)
                if detected_lang == target_language:
                    filtered_elements.append(element)
            except Exception:
                continue
        logger.debug(f"Language filtering: {len(filtered_elements)}/{len(elements)} elements kept")
        return filtered_elements
    
    def _extract_content(self, elements: List) -> List[Dict]:
        content = []
        current_title = None
        current_paragraph = []

        for element in elements:
            if element.category == "Title":
                if current_title is not None:
                    content.append({"title": current_title, "text": current_paragraph})
                elif current_paragraph:
                    content.append({"title": "Default", "text": current_paragraph})

                current_title = element.text
                current_paragraph = []

            elif element.category == "NarrativeText":
                current_paragraph.append(element.text)

        if current_title is not None:
            content.append({"title": current_title, "text": current_paragraph})

        return content
    
    def _create_markdown(self, content: List[Dict]) -> str:
        md_lines = []
        for item in content:
            if isinstance(item['text'], list):
                text = "\n".join(item['text'])
            else:
                text = item['text']

            combined = f"# {item['title']}\n{text}"
            md_lines.append(combined)
        
        return "\n".join(md_lines)
    
    def _create_content_string(self, elements: List) -> str:
        return " ".join(element.text for element in elements)