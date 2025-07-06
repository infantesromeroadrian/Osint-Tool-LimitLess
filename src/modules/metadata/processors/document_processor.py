"""
Document Metadata Processor
Procesador simple para documentos y archivos de texto
"""

from typing import Dict, Any
from pathlib import Path
from ..base_processor import BaseMetadataProcessor

class DocumentMetadataProcessor(BaseMetadataProcessor):
    """
    Procesador para documentos básicos
    Maneja archivos de texto y documentos simples
    """
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.md', '.log'}
    
    def __init__(self):
        super().__init__("document")
    
    def can_process(self, file_path: Path) -> bool:
        """Verificar si puede procesar el documento"""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS
    
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extraer metadatos básicos del documento"""
        try:
            result = {
                "type": "document",
                "encoding": self._detect_encoding(file_path) if self._is_text_file(file_path) else "unknown",
                "line_count": self._count_lines(file_path) if self._is_text_file(file_path) else None,
                "word_count": self._count_words(file_path) if self._is_text_file(file_path) else None,
                "details": f"Basic {file_path.suffix} document metadata"
            }
            
            self.log_success(file_path, 3)
            return result
            
        except Exception as e:
            error_msg = str(e)
            self.log_error(file_path, error_msg)
            return self.get_error_response(error_msg)
    
    def _is_text_file(self, file_path: Path) -> bool:
        """Verificar si es un archivo de texto plano"""
        return file_path.suffix.lower() in {'.txt', '.md', '.log'}
    
    def _detect_encoding(self, file_path: Path) -> str:
        """Detectar codificación de archivos de texto"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(1024)
            
            # Intentar codificaciones comunes
            encodings = ['utf-8', 'ascii', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    raw_data.decode(encoding)
                    return encoding
                except UnicodeDecodeError:
                    continue
            
            return "unknown"
            
        except Exception:
            return "unknown"
    
    def _count_lines(self, file_path: Path) -> int:
        """Contar líneas en archivo de texto"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0
    
    def _count_words(self, file_path: Path) -> int:
        """Contar palabras en archivo de texto"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return len(content.split())
        except Exception:
            return 0 