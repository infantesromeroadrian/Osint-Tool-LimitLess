"""
Base Processor for Metadata Extraction
Clase abstracta para procesadores de metadatos
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class BaseMetadataProcessor(ABC):
    """
    Clase base abstracta para procesadores de metadatos
    Define la interfaz común para todos los tipos de archivos
    """
    
    def __init__(self, file_type: str):
        self.file_type = file_type
        self.logger = logging.getLogger(f"{__name__}.{file_type}")
    
    @abstractmethod
    def can_process(self, file_path: Path) -> bool:
        """
        Verificar si este procesador puede manejar el archivo
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            bool: True si puede procesar, False si no
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extraer metadatos específicos del archivo
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Dict con metadatos extraídos
        """
        pass
    
    def get_error_response(self, error: str, note: str = None) -> Dict[str, Any]:
        """
        Generar respuesta de error estandarizada
        
        Args:
            error: Mensaje de error
            note: Nota adicional opcional
            
        Returns:
            Dict con formato de error estándar
        """
        response = {
            "type": self.file_type,
            "error": error
        }
        if note:
            response["note"] = note
        return response
    
    def log_success(self, file_path: Path, data_count: int = 0):
        """Log de éxito con formato consistente"""
        self.logger.info(f"✅ {self.file_type} metadata extracted: {file_path.name} ({data_count} fields)")
    
    def log_error(self, file_path: Path, error: str):
        """Log de error con formato consistente"""
        self.logger.error(f"❌ {self.file_type} metadata error: {file_path.name} - {error}") 