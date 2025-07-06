"""
Simple Case Manager 
Maneja metadatos y contexto de casos sin duplicar funcionalidad RAG
Gestión de casos activos y múltiples casos
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

class SimpleCaseManager:
    """
    Manager simple de casos
    Solo maneja metadatos y contexto, no duplica RAG
    Gestiona casos activos y múltiples casos
    """
    
    def __init__(self, cases_dir: str = "data/cases"):
        """Inicializar manager de casos"""
        self.cases_dir = Path(cases_dir)
        self.cases_dir.mkdir(exist_ok=True)
        self.active_cases = {}  # {session_id: case_id}
        
        # Crear caso inicial si no existe (compatibilidad)
        self._ensure_initial_case()
        
        logger.info(f"✅ Simple Case Manager inicializado: {cases_dir}")
    
    def _ensure_initial_case(self):
        """Asegurar que existe el caso inicial para compatibilidad"""
        try:
            initial_case_file = self.cases_dir / "aeronave_vigilancia_001.md"
            metadata_file = self.cases_dir / "aeronave_vigilancia_001_metadata.json"
            
            # Si existe el archivo MD pero no el metadata, crear metadata
            if initial_case_file.exists() and not metadata_file.exists():
                case_data = {
                    "case_id": "aeronave_vigilancia_001",
                    "title": "Análisis de Aeronave Interceptada",
                    "description": "Grabaciones de aeropuerto interceptadas que requieren análisis inmediato.",
                    "case_type": "surveillance",
                    "created_at": datetime.now().isoformat(),
                    "status": "active",
                    "analyses_count": 0
                }
                
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(case_data, f, indent=2, ensure_ascii=False)
                
                logger.info("✅ Metadata creado para caso inicial existente")
                
        except Exception as e:
            logger.error(f"❌ Error asegurando caso inicial: {e}")
    
    def create_case(self, title: str, description: str = "", case_type: str = "intelligence") -> Dict[str, Any]:
        """Crear nuevo caso"""
        try:
            # Generar ID único para el caso
            case_id = f"{case_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Metadata del caso
            case_data = {
                "case_id": case_id,
                "title": title,
                "description": description,
                "case_type": case_type,
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "analyses_count": 0
            }
            
            # Guardar metadata del caso
            metadata_file = self.cases_dir / f"{case_id}_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(case_data, f, indent=2, ensure_ascii=False)
            
            # Crear archivo de briefing básico
            briefing_file = self.cases_dir / f"{case_id}.md"
            briefing_content = f"""# CASO: {title.upper()}

## 📋 INFORMACIÓN DEL CASO

**Case ID:** {case_id}  
**Tipo:** {case_type}  
**Estado:** Activo  
**Creado:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  

## 📝 DESCRIPCIÓN

{description}

## 📁 EVIDENCIA
- [ ] Documentos por agregar
- [ ] Imágenes por analizar
- [ ] Datos por procesar

## 📊 ANÁLISIS
_Los resultados de análisis aparecerán aquí_

---
**Última actualización:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            with open(briefing_file, 'w', encoding='utf-8') as f:
                f.write(briefing_content)
            
            logger.info(f"✅ Caso creado: {case_id} - {title}")
            return {"success": True, "case_id": case_id, "case_data": case_data}
            
        except Exception as e:
            logger.error(f"❌ Error creando caso: {e}")
            return {"success": False, "error": str(e)}
    
    def get_all_cases(self) -> List[Dict[str, Any]]:
        """Obtener lista de todos los casos"""
        try:
            cases = []
            for metadata_file in self.cases_dir.glob("*_metadata.json"):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    case_data = json.load(f)
                    cases.append(case_data)
            
            # Ordenar por fecha de creación (más recientes primero)
            cases.sort(key=lambda x: x['created_at'], reverse=True)
            return cases
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo casos: {e}")
            return []
    
    def set_active_case(self, session_id: str, case_id: str) -> bool:
        """Establecer caso activo para una sesión"""
        try:
            # Verificar que el caso existe
            metadata_file = self.cases_dir / f"{case_id}_metadata.json"
            if not metadata_file.exists():
                logger.error(f"❌ Caso no encontrado: {case_id}")
                return False
            
            self.active_cases[session_id] = case_id
            logger.info(f"✅ Caso activo establecido: {case_id} para sesión {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error estableciendo caso activo: {e}")
            return False
    
    def get_active_case(self, session_id: str) -> Optional[str]:
        """Obtener caso activo para una sesión"""
        return self.active_cases.get(session_id)
    
    def get_case_metadata(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Obtener metadata de un caso específico"""
        try:
            metadata_file = self.cases_dir / f"{case_id}_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"❌ Error obteniendo metadata del caso: {e}")
            return None
    
    def load_case_context(self, case_id: str) -> Optional[str]:
        """Cargar contexto de caso desde archivo"""
        try:
            case_file = self.cases_dir / f"{case_id}.md"
            if case_file.exists():
                with open(case_file, 'r', encoding='utf-8') as f:
                    return f.read()
            return None
        except Exception as e:
            logger.error(f"❌ Error cargando caso {case_id}: {e}")
            return None
    
    def save_analysis_result(self, case_id: str, analysis_type: str, result: Dict[str, Any]):
        """Guardar resultado de análisis en archivo del caso"""
        try:
            results_file = self.cases_dir / f"{case_id}_results.json"
            
            # Cargar resultados existentes
            results = {}
            if results_file.exists():
                with open(results_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)
            
            # Agregar nuevo resultado
            if analysis_type not in results:
                results[analysis_type] = []
            
            results[analysis_type].append({
                "timestamp": datetime.now().isoformat(),
                "result": result
            })
            
            # Guardar
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Resultado guardado: {case_id} - {analysis_type}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando resultado: {e}")
    
    def get_case_summary(self, case_id: str) -> Dict[str, Any]:
        """Obtener resumen simple del caso"""
        try:
            results_file = self.cases_dir / f"{case_id}_results.json"
            
            if not results_file.exists():
                return {"error": "No results found for case"}
            
            with open(results_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            summary = {
                "case_id": case_id,
                "analysis_types": list(results.keys()),
                "total_analyses": sum(len(analyses) for analyses in results.values()),
                "last_updated": max(
                    analysis["timestamp"] 
                    for analyses in results.values() 
                    for analysis in analyses
                ) if results else None
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo resumen: {e}")
            return {"error": str(e)}

# Instancia global
case_manager = SimpleCaseManager() 