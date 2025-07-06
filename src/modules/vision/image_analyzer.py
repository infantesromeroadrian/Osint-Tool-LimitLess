"""
Generic Image Analysis Module
Análisis de imágenes usando OpenAI Vision API
Versátil para cualquier tipo de imagen y contexto
"""

import logging
import base64
from typing import Dict, Any, Optional
from datetime import datetime

from openai import OpenAI
from src.config.settings import settings

logger = logging.getLogger(__name__)

class GenericImageAnalyzer:
    """
    Analizador genérico de imágenes usando OpenAI Vision
    Módulo simple y especializado para cualquier tipo de imagen
    """
    
    def __init__(self):
        """Inicializar analizador de visión"""
        try:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY requerida")
            
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("✅ Generic Image Analyzer inicializado")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Image Analyzer: {e}")
            raise

    def analyze_image(self, image_path: str, case_context: str = "", analysis_type: str = "general") -> Dict[str, Any]:
        """
        Analizar imagen con contexto de caso y tipo específico
        
        Args:
            image_path: Ruta de la imagen
            case_context: Contexto del caso para análisis específico
            analysis_type: Tipo de análisis (general, aircraft, person, vehicle, document, etc.)
            
        Returns:
            Dict con análisis detallado
        """
        start_time = datetime.now()
        
        try:
            # Codificar imagen
            image_data = self._encode_image(image_path)
            
            # Crear prompt especializado según el tipo
            prompt = self._create_analysis_prompt(case_context, analysis_type)
            
            # Ejecutar análisis
            response = self.client.chat.completions.create(
                model=settings.OPENAI_VISION_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto analista de inteligencia especializado en análisis visual forense. Proporciona análisis detallado, técnico y preciso."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            analysis = response.choices[0].message.content
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Extraer elementos específicos según el tipo
            extracted_info = self._extract_structured_info(analysis, analysis_type)
            
            result = {
                "analysis": analysis,
                "extracted_info": extracted_info,
                "analysis_type": analysis_type,
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat(),
                "model_used": settings.OPENAI_VISION_MODEL,
                "success": True
            }
            
            logger.info(f"✅ Análisis de imagen completado en {processing_time:.2f}s - Tipo: {analysis_type}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error analizando imagen: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "analysis": f"Error durante análisis: {str(e)}",
                "extracted_info": {},
                "analysis_type": analysis_type,
                "processing_time": processing_time,
                "error": True,
                "success": False
            }

    def _encode_image(self, image_path: str) -> str:
        """Codificar imagen en base64"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"❌ Error codificando imagen: {e}")
            raise

    def _create_analysis_prompt(self, case_context: str, analysis_type: str) -> str:
        """Crear prompt especializado según el tipo de análisis"""
        
        prompts = {
            "aircraft": """
            ANALIZA ESTA AERONAVE CON MÁXIMO DETALLE TÉCNICO:
            
            🎯 OBJETIVOS:
            1. Identificar MODELO y TIPO de aeronave
            2. Determinar OPERADOR/AEROLÍNEA
            3. Extraer NÚMERO DE REGISTRO/COLA
            4. Analizar LIBREA y MARCADORES VISUALES
            
            📋 ANÁLISIS TÉCNICO:
            - Configuración del ala, motores, fuselaje, cola
            - Detalles de librea (colores, patrones, logos)
            - Marcas de registro visibles
            - Estado y condición aparente
            """,
            
            "person": """
            ANALIZA ESTA IMAGEN DE PERSONA CON DETALLE FORENSE:
            
            🎯 OBJETIVOS:
            1. Descripción física detallada
            2. Vestimenta y accesorios
            3. Contexto y ubicación
            4. Elementos identificativos
            
            📋 ANÁLISIS:
            - Características físicas observables
            - Ropa, accesorios, objetos portados
            - Postura, gestos, actividades
            - Elementos del entorno
            """,
            
            "vehicle": """
            ANALIZA ESTE VEHÍCULO CON DETALLE TÉCNICO:
            
            🎯 OBJETIVOS:
            1. Identificar MARCA, MODELO y AÑO
            2. Extraer MATRÍCULA/PLACA
            3. Analizar COLOR y CARACTERÍSTICAS
            4. Estado y modificaciones
            
            📋 ANÁLISIS:
            - Tipo de vehículo, marca, modelo estimado
            - Placas, identificadores visibles
            - Color, daños, modificaciones
            - Contexto y ubicación
            """,
            
            "document": """
            ANALIZA ESTE DOCUMENTO CON PRECISIÓN FORENSE:
            
            🎯 OBJETIVOS:
            1. Extraer TEXTO legible
            2. Identificar TIPO de documento
            3. Detectar ELEMENTOS de seguridad
            4. Analizar AUTENTICIDAD
            
            📋 ANÁLISIS:
            - Texto completo legible
            - Tipo, formato, estructura
            - Sellos, firmas, marcas de agua
            - Señales de alteración
            """,
            
            "general": """
            ANALIZA ESTA IMAGEN CON DETALLE INVESTIGATIVO:
            
            🎯 OBJETIVOS:
            1. Descripción COMPLETA de la escena
            2. Identificar OBJETOS y PERSONAS
            3. Analizar CONTEXTO y UBICACIÓN
            4. Detectar DETALLES relevantes
            
            📋 ANÁLISIS:
            - Descripción general de la imagen
            - Objetos, personas, actividades visibles
            - Ubicación, ambiente, contexto
            - Detalles específicos de interés
            """
        }
        
        base_prompt = prompts.get(analysis_type, prompts["general"])
        
        if case_context:
            base_prompt += f"\n\n📁 CONTEXTO DEL CASO:\n{case_context}"
        
        base_prompt += "\n\nProporciona análisis estructurado, detallado y profesional."
        
        return base_prompt

    def _extract_structured_info(self, analysis: str, analysis_type: str) -> Dict[str, Any]:
        """Extraer información estructurada según el tipo de análisis"""
        try:
            if analysis_type == "aircraft":
                return self._extract_aircraft_info(analysis)
            elif analysis_type == "vehicle":
                return self._extract_vehicle_info(analysis)
            elif analysis_type == "person":
                return self._extract_person_info(analysis)
            elif analysis_type == "document":
                return self._extract_document_info(analysis)
            else:
                return self._extract_general_info(analysis)
                
        except Exception as e:
            logger.error(f"❌ Error extrayendo información: {e}")
            return {}

    def _extract_aircraft_info(self, analysis: str) -> Dict[str, Any]:
        """Extraer información específica de aeronaves"""
        return {
            "aircraft_type": self._extract_field(analysis, ["tipo", "modelo", "aircraft", "model"]),
            "operator": self._extract_field(analysis, ["operador", "aerolínea", "airline", "operator"]),
            "registration": self._extract_field(analysis, ["registro", "cola", "registration", "tail"]),
            "manufacturer": self._extract_field(analysis, ["fabricante", "manufacturer", "boeing", "airbus"]),
            "engines": self._extract_field(analysis, ["motores", "engines", "engine"]),
            "livery": self._extract_field(analysis, ["librea", "livery", "colores", "colors"])
        }

    def _extract_vehicle_info(self, analysis: str) -> Dict[str, Any]:
        """Extraer información específica de vehículos"""
        return {
            "make_model": self._extract_field(analysis, ["marca", "modelo", "make", "model"]),
            "license_plate": self._extract_field(analysis, ["matrícula", "placa", "license", "plate"]),
            "color": self._extract_field(analysis, ["color", "colour"]),
            "year": self._extract_field(analysis, ["año", "year"]),
            "type": self._extract_field(analysis, ["tipo", "type", "sedan", "suv", "truck"])
        }

    def _extract_person_info(self, analysis: str) -> Dict[str, Any]:
        """Extraer información específica de personas"""
        return {
            "physical_description": self._extract_field(analysis, ["físico", "physical", "altura", "height"]),
            "clothing": self._extract_field(analysis, ["vestimenta", "ropa", "clothing", "shirt"]),
            "accessories": self._extract_field(analysis, ["accesorios", "accessories", "gafas", "glasses"]),
            "activity": self._extract_field(analysis, ["actividad", "activity", "acción", "action"]),
            "location": self._extract_field(analysis, ["ubicación", "location", "lugar", "place"])
        }

    def _extract_document_info(self, analysis: str) -> Dict[str, Any]:
        """Extraer información específica de documentos"""
        return {
            "document_type": self._extract_field(analysis, ["tipo", "type", "documento", "document"]),
            "text_content": self._extract_field(analysis, ["texto", "text", "contenido", "content"]),
            "signatures": self._extract_field(analysis, ["firma", "signature", "firmas", "signatures"]),
            "stamps": self._extract_field(analysis, ["sello", "stamp", "sellos", "stamps"]),
            "authenticity": self._extract_field(analysis, ["autenticidad", "authenticity", "genuine", "fake"])
        }

    def _extract_general_info(self, analysis: str) -> Dict[str, Any]:
        """Extraer información general"""
        return {
            "main_objects": self._extract_field(analysis, ["objeto", "objects", "elementos", "items"]),
            "people": self._extract_field(analysis, ["persona", "people", "individuals", "subjects"]),
            "location": self._extract_field(analysis, ["ubicación", "location", "lugar", "environment"]),
            "activity": self._extract_field(analysis, ["actividad", "activity", "acción", "action"]),
            "notable_details": self._extract_field(analysis, ["detalle", "details", "notable", "important"])
        }

    def _extract_field(self, text: str, keywords: list) -> Optional[str]:
        """Extraer campo específico basado en palabras clave"""
        try:
            text_lower = text.lower()
            for keyword in keywords:
                if keyword in text_lower:
                    sentences = text.split('.')
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            return sentence.strip()
            return None
        except:
            return None

# Instancia global
image_analyzer = GenericImageAnalyzer() 