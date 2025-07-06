"""
Modular File Metadata Extractor
Extractor refactorizado usando patrón de procesadores especializados
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# Imports de la nueva arquitectura modular
from .processors import ImageMetadataProcessor, MediaMetadataProcessor, DocumentMetadataProcessor
from .utils import extract_basic_metadata, get_file_category, generate_metadata_summary
from .base_processor import BaseMetadataProcessor

logger = logging.getLogger(__name__)

class ModularMetadataExtractor:
    """
    Extractor modular de metadatos usando procesadores especializados
    Arquitectura limpia y extensible
    """
    
    def __init__(self):
        """Inicializar extractor con procesadores especializados"""
        self.processors: List[BaseMetadataProcessor] = [
            ImageMetadataProcessor(),
            MediaMetadataProcessor(),
            DocumentMetadataProcessor()
        ]
        
        # Log de capacidades
        self._log_capabilities()
        logger.info("✅ Modular Metadata Extractor initialized")
    
    def extract_metadata(self, file_path: str, case_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Extraer metadatos completos usando procesadores especializados
        
        Args:
            file_path: Ruta del archivo
            case_id: ID del caso para contexto
            
        Returns:
            Dict con metadatos extraídos
        """
        start_time = datetime.now()
        
        try:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                return self._create_error_response(file_path, "File not found")
            
            # Metadatos básicos (común para todos)
            basic_metadata = extract_basic_metadata(file_path_obj)
            
            # Metadatos específicos usando procesador apropiado
            specific_metadata = self._extract_specific_metadata(file_path_obj)
            
            # Calcular tiempo de procesamiento
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Combinar resultados
            result = {
                "file_path": str(file_path_obj),
                "case_id": case_id,
                "basic": basic_metadata,
                "specific": specific_metadata,
                "extraction_timestamp": datetime.now().isoformat(),
                "processing_time": processing_time,
                "success": True
            }
            
            logger.info(f"✅ Metadata extracted: {file_path_obj.name} ({processing_time:.2f}s)")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Metadata extraction failed: {e}")
            
            return self._create_error_response(file_path, str(e), processing_time)
    
    def _extract_specific_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extraer metadatos específicos usando el procesador apropiado
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Dict con metadatos específicos
        """
        # Buscar procesador apropiado
        for processor in self.processors:
            if processor.can_process(file_path):
                return processor.extract_metadata(file_path)
        
        # No hay procesador específico disponible
        return {
            "type": "unknown",
            "details": f"No specialized processor for {file_path.suffix}",
            "category": get_file_category(file_path.suffix)
        }
    
    def get_summary(self, metadata: Dict[str, Any]) -> str:
        """
        Generar resumen legible de metadatos
        Delegado a utilidades comunes
        """
        return generate_metadata_summary(metadata)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del sistema de extracción
        """
        return {
            "total_processors": len(self.processors),
            "processor_types": [p.file_type for p in self.processors],
            "supported_categories": ["image", "video", "audio", "document"],
            "architecture": "modular_specialized_processors",
            "version": "2.0_modular"
        }
    
    def _log_capabilities(self):
        """Log de capacidades de los procesadores"""
        capabilities = []
        for processor in self.processors:
            capabilities.append(f"{processor.file_type} processor")
        
        logger.info(f"📋 Loaded processors: {', '.join(capabilities)}")
    
    def _create_error_response(self, file_path: str, error: str, processing_time: float = 0.0) -> Dict[str, Any]:
        """
        Crear respuesta de error estandarizada
        
        Args:
            file_path: Ruta del archivo
            error: Mensaje de error
            processing_time: Tiempo de procesamiento
            
        Returns:
            Dict con formato de error estándar
        """
        return {
            "file_path": file_path,
            "error": error,
            "success": False,
            "extraction_timestamp": datetime.now().isoformat(),
            "processing_time": processing_time
        }

# Instancia global del extractor modular
modular_extractor = ModularMetadataExtractor() 