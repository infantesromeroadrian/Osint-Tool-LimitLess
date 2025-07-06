"""
LimitLess OSINT Tool - Aplicación simplificada con LangChain RAG
Solo funcionalidades esenciales + Vision Analysis
"""

import logging
import os
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime
from werkzeug.utils import secure_filename
import uuid

# Configuración
from src.config.settings import settings

# Sistema RAG simplificado
from src.modules.rag.langchain_rag import rag_system

# Sistema de vision genérico
from src.modules.vision.image_analyzer import image_analyzer

# Manager simple de casos
from src.modules.cases.case_manager import case_manager

# Extractor de metadatos
from src.modules.metadata.extractor import modular_extractor as metadata_extractor

# ✅ NUEVO: Sistema de conversación
class ConversationManager:
    """Gestor de conversaciones por sesión"""
    
    def __init__(self):
        self.conversations = {}  # session_id -> list of messages
        self.message_reactions = {}  # session_id -> {message_id: {reaction: count}}
    
    def add_message(self, session_id: str, role: str, content: str, metadata: dict = None):
        """Agregar mensaje a la conversación"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
            "message_id": str(uuid.uuid4()),  # ✅ ID único para reacciones
            "reactions": {}  # ✅ Reacciones del mensaje
        }
        
        self.conversations[session_id].append(message)
        
        # Mantener solo los últimos 20 mensajes para evitar context overflow
        if len(self.conversations[session_id]) > 20:
            self.conversations[session_id] = self.conversations[session_id][-20:]
    
    def add_reaction(self, session_id: str, message_id: str, reaction: str) -> bool:
        """Agregar reacción a un mensaje"""
        try:
            if session_id not in self.conversations:
                return False
            
            # Buscar el mensaje
            for message in self.conversations[session_id]:
                if message.get("message_id") == message_id:
                    if "reactions" not in message:
                        message["reactions"] = {}
                    
                    # Toggle reaction (si ya existe, la quita; si no, la agrega)
                    if reaction in message["reactions"]:
                        message["reactions"][reaction] += 1
                    else:
                        message["reactions"][reaction] = 1
                    
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ Error adding reaction: {e}")
            return False
    
    def get_conversation(self, session_id: str) -> list:
        """Obtener historial de conversación"""
        return self.conversations.get(session_id, [])
    
    def clear_conversation(self, session_id: str):
        """Limpiar conversación"""
        if session_id in self.conversations:
            del self.conversations[session_id]
        if session_id in self.message_reactions:
            del self.message_reactions[session_id]
    
    def get_conversation_context(self, session_id: str, max_messages: int = 10) -> str:
        """Obtener contexto de conversación como string"""
        messages = self.get_conversation(session_id)
        if not messages:
            return ""
        
        # Tomar los últimos N mensajes
        recent_messages = messages[-max_messages:]
        
        context_parts = []
        for msg in recent_messages:
            role_label = "Usuario" if msg["role"] == "user" else "Asistente"
            context_parts.append(f"{role_label}: {msg['content']}")
        
        return "\n".join(context_parts)
    
    def generate_suggestions(self, session_id: str, latest_content: str, analysis_type: str = None) -> list:
        """✅ NUEVO: Generar sugerencias proactivas basadas en contexto"""
        suggestions = []
        
        try:
            content_lower = latest_content.lower()
            
            # ✅ Sugerencias basadas en contenido
            if "gps" in content_lower or "coordenadas" in content_lower or "ubicación" in content_lower:
                suggestions.append({
                    "text": "¿Quieres que analice la ubicación GPS de esta información?",
                    "action": "geospatial_analysis",
                    "icon": "🗺️"
                })
            
            if "imagen" in content_lower or "foto" in content_lower or "aircraft" in content_lower:
                suggestions.append({
                    "text": "¿Te gustaría analizar una imagen relacionada?",
                    "action": "image_analysis", 
                    "icon": "🖼️"
                })
            
            if "video" in content_lower or "mp4" in content_lower or "metadata" in content_lower:
                suggestions.append({
                    "text": "¿Quieres extraer metadatos de un archivo?",
                    "action": "metadata_extraction",
                    "icon": "📁"
                })
            
            if "persona" in content_lower or "sospechoso" in content_lower or "individuo" in content_lower:
                suggestions.append({
                    "text": "¿Necesitas crear un perfil de esta persona?",
                    "action": "person_profile",
                    "icon": "👤"
                })
            
            # ✅ Sugerencias basadas en tipo de análisis
            if analysis_type == "image_analysis":
                suggestions.extend([
                    {
                        "text": "¿Quieres buscar imágenes similares en el caso?",
                        "action": "similar_search",
                        "icon": "🔍"
                    },
                    {
                        "text": "¿Te interesa extraer texto de la imagen?",
                        "action": "ocr_analysis", 
                        "icon": "📝"
                    }
                ])
            
            if analysis_type == "metadata_extraction":
                suggestions.extend([
                    {
                        "text": "¿Quieres comparar con metadatos de otros archivos?",
                        "action": "metadata_comparison",
                        "icon": "🔗"
                    },
                    {
                        "text": "¿Te interesa crear una línea de tiempo?",
                        "action": "timeline_creation",
                        "icon": "🕰️"
                    }
                ])
            
            # ✅ Sugerencias contextuales generales
            conversation = self.get_conversation(session_id)
            if len(conversation) > 3:
                suggestions.append({
                    "text": "¿Quieres un resumen de la conversación?",
                    "action": "conversation_summary",
                    "icon": "📊"
                })
            
            return suggestions[:3]  # Máximo 3 sugerencias
            
        except Exception as e:
            logger.error(f"❌ Error generating suggestions: {e}")
            return []

# Instancia global del conversation manager
conversation_manager = ConversationManager()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Crear aplicación Flask"""
    app = Flask(__name__)
    app.secret_key = settings.SECRET_KEY
    
    def get_session_id():
        """Obtener o crear session ID"""
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        return session['session_id']
    
    @app.route('/')
    def index():
        """Página principal"""
        return render_template('index.html')
    
    @app.route('/process_text', methods=['POST'])
    def process_text():
        """Procesar texto y agregar al RAG"""
        try:
            data = request.get_json()
            text = data.get('text', '').strip()
            
            if not text:
                return jsonify({
                    "success": False,
                    "error": "Texto requerido"
                }), 400
            
            # Agregar texto al sistema RAG
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "source": "manual_input"
            }
            
            success = rag_system.add_documents([text], [metadata])
            
            if success:
                logger.info(f"✅ Texto agregado al RAG: {text[:100]}...")
                return jsonify({
                    "success": True,
                    "message": "Texto procesado y agregado al sistema"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Error agregando texto al sistema"
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Error procesando texto: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/query', methods=['POST'])
    def query_rag():
        """Ejecutar consulta RAG (legacy endpoint)"""
        try:
            data = request.get_json()
            question = data.get('question', '').strip()
            
            if not question:
                return jsonify({
                    "success": False,
                    "error": "Pregunta requerida"
                }), 400
            
            # Ejecutar consulta
            result = rag_system.query(question)
            
            return jsonify({
                "success": True,
                "result": result
            })
            
        except Exception as e:
            logger.error(f"❌ Error en consulta: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/chat', methods=['POST'])
    def chat_conversation():
        """Chat conversacional con contexto RAG + historial"""
        try:
            data = request.get_json()
            message = data.get('message', '').strip()
            
            if not message:
                return jsonify({
                    "success": False,
                    "error": "Mensaje requerido"
                }), 400
            
            session_id = get_session_id()
            case_id = case_manager.get_active_case(session_id)
            
            # Agregar mensaje del usuario a la conversación
            conversation_manager.add_message(session_id, "user", message)
            
            # Obtener contexto de conversación previa
            conversation_context = conversation_manager.get_conversation_context(session_id, max_messages=8)
            
            # Obtener contexto del caso activo
            case_context = ""
            if case_id:
                case_data = case_manager.get_case_metadata(case_id)
                case_context = f"Caso activo: {case_data.get('title', case_id)} ({case_data.get('case_type', 'general')})"
                if case_data.get('description'):
                    case_context += f" - {case_data['description']}"
            
            # Crear pregunta enriquecida con contexto
            enriched_question = message
            if conversation_context:
                enriched_question = f"""Contexto de conversación:
{conversation_context}

{f"Contexto del caso: {case_context}" if case_context else ""}

Pregunta actual: {message}"""
            elif case_context:
                enriched_question = f"""Contexto del caso: {case_context}

Pregunta: {message}"""
            
            # Ejecutar consulta RAG con contexto enriquecido
            result = rag_system.query(enriched_question)
            
            # Agregar respuesta del asistente a la conversación
            conversation_manager.add_message(
                session_id, 
                "assistant", 
                result["answer"],
                metadata={
                    "rag_sources": len(result.get("source_documents", [])),
                    "processing_time": result.get("processing_time"),
                    "case_id": case_id
                }
            )
            
            # Obtener historial completo de conversación para el frontend
            full_conversation = conversation_manager.get_conversation(session_id)
            
            # ✅ NUEVO: Generar sugerencias proactivas
            suggestions = conversation_manager.generate_suggestions(session_id, result["answer"], "chat_response")
            
            return jsonify({
                "success": True,
                "result": result,
                "conversation": full_conversation,
                "case_context": case_context,
                "has_conversation_context": bool(conversation_context),
                "suggestions": suggestions  # ✅ Sugerencias incluidas automáticamente
            })
            
        except Exception as e:
            logger.error(f"❌ Error en chat: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/chat/clear', methods=['POST'])
    def clear_chat():
        """Limpiar historial de conversación"""
        try:
            session_id = get_session_id()
            conversation_manager.clear_conversation(session_id)
            
            return jsonify({
                "success": True,
                "message": "Conversación limpiada"
            })
            
        except Exception as e:
            logger.error(f"❌ Error limpiando chat: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/chat/history', methods=['GET'])
    def get_chat_history():
        """Obtener historial de conversación"""
        try:
            session_id = get_session_id()
            conversation = conversation_manager.get_conversation(session_id)
            
            return jsonify({
                "success": True,
                "conversation": conversation
            })
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo historial: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/chat/react', methods=['POST'])
    def add_message_reaction():
        """✅ NUEVO: Agregar reacción a un mensaje"""
        try:
            data = request.get_json()
            message_id = data.get('message_id')
            reaction = data.get('reaction')
            
            if not message_id or not reaction:
                return jsonify({
                    "success": False,
                    "error": "message_id y reaction requeridos"
                }), 400
            
            # Validar reaction permitida
            allowed_reactions = ['👍', '❤️', '🔍', '⚠️', '📊']
            if reaction not in allowed_reactions:
                return jsonify({
                    "success": False,
                    "error": f"Reacción no permitida. Usar: {', '.join(allowed_reactions)}"
                }), 400
            
            session_id = get_session_id()
            success = conversation_manager.add_reaction(session_id, message_id, reaction)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "Reacción agregada"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Mensaje no encontrado"
                }), 404
                
        except Exception as e:
            logger.error(f"❌ Error agregando reacción: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/suggestions', methods=['POST'])
    def get_proactive_suggestions():
        """✅ NUEVO: Obtener sugerencias proactivas"""
        try:
            data = request.get_json()
            content = data.get('content', '')
            analysis_type = data.get('analysis_type')
            
            session_id = get_session_id()
            suggestions = conversation_manager.generate_suggestions(session_id, content, analysis_type)
            
            return jsonify({
                "success": True,
                "suggestions": suggestions
            })
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo sugerencias: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/stats')
    def get_stats():
        """Obtener estadísticas del sistema"""
        try:
            stats = rag_system.get_stats()
            return jsonify({
                "success": True,
                "stats": stats
            })
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/cases', methods=['GET'])
    def get_cases():
        """Obtener lista de casos y caso activo"""
        try:
            session_id = get_session_id()
            all_cases = case_manager.get_all_cases()
            active_case_id = case_manager.get_active_case(session_id)
            active_case_data = None
            
            if active_case_id:
                active_case_data = case_manager.get_case_metadata(active_case_id)
            
            return jsonify({
                "success": True,
                "cases": all_cases,
                "active_case": active_case_data
            })
        except Exception as e:
            logger.error(f"❌ Error obteniendo casos: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/cases', methods=['POST'])
    def create_case():
        """Crear nuevo caso"""
        try:
            data = request.get_json()
            title = data.get('title', '').strip()
            description = data.get('description', '').strip()
            case_type = data.get('case_type', 'intelligence')
            
            if not title:
                return jsonify({
                    "success": False,
                    "error": "Título del caso requerido"
                }), 400
            
            # Crear caso
            result = case_manager.create_case(title, description, case_type)
            
            if result["success"]:
                # Establecer como caso activo automáticamente
                session_id = get_session_id()
                case_manager.set_active_case(session_id, result["case_id"])
                
                logger.info(f"✅ Caso creado y activado: {result['case_id']}")
                return jsonify(result)
            else:
                return jsonify(result), 500
                
        except Exception as e:
            logger.error(f"❌ Error creando caso: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/cases/<case_id>/activate', methods=['POST'])
    def activate_case(case_id):
        """Activar un caso específico"""
        try:
            session_id = get_session_id()
            success = case_manager.set_active_case(session_id, case_id)
            
            if success:
                case_data = case_manager.get_case_metadata(case_id)
                return jsonify({
                    "success": True,
                    "message": f"Caso {case_id} activado",
                    "active_case": case_data
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Caso no encontrado"
                }), 404
                
        except Exception as e:
            logger.error(f"❌ Error activando caso: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/analyze_image', methods=['POST'])
    def analyze_image():
        """Analizar imagen con contexto de caso y tipo específico"""
        try:
            # Verificar si se subió archivo
            if 'image' not in request.files:
                return jsonify({
                    "success": False,
                    "error": "No se encontró archivo de imagen"
                }), 400
            
            file = request.files['image']
            session_id = get_session_id()
            case_id = case_manager.get_active_case(session_id)
            
            # ✅ CAMBIO: Permitir análisis sin caso activo
            if not case_id:
                logger.info("⚠️ Análisis de imagen sin caso activo - modo rápido")
                case_id = None  # Análisis rápido sin caso
            
            if file.filename == '':
                return jsonify({
                    "success": False,
                    "error": "No se seleccionó archivo"
                }), 400
            
            # Obtener tipo de análisis del formulario (por defecto: general)
            analysis_type = request.form.get('analysis_type', 'general')
            
            # Guardar archivo temporal
            filename = secure_filename(file.filename)
            temp_path = f"data/temp_{filename}"
            file.save(temp_path)
            
            try:
                # Cargar contexto del caso (si existe)
                case_context = ""
                if case_id:
                    case_context = case_manager.load_case_context(case_id)
                
                # Contexto por defecto si no hay caso
                if not case_context:
                    case_context = f"Análisis rápido de imagen: {filename}"
                
                # Analizar imagen con el tipo específico
                result = image_analyzer.analyze_image(
                    temp_path, 
                    case_context,
                    analysis_type
                )
                
                # Extraer metadatos del archivo
                metadata_result = metadata_extractor.extract_metadata(temp_path, case_id)
                result["metadata"] = metadata_result
                
                # Guardar resultado en caso solo si hay caso activo
                if result.get("success") and case_id:
                    case_manager.save_analysis_result(case_id, "image_analysis", result)
                    
                    # Agregar análisis al RAG para futuras consultas
                    rag_metadata = {
                        "case_id": case_id,
                        "analysis_type": f"image_analysis_{analysis_type}",
                        "timestamp": datetime.now().isoformat(),
                        "image_file": filename
                    }
                    
                    rag_system.add_documents([result["analysis"]], [rag_metadata])
                    logger.info(f"✅ Análisis {analysis_type} agregado al RAG para caso {case_id}")
                elif result.get("success"):
                    # Análisis rápido sin caso - solo agregar al RAG sin caso
                    rag_metadata = {
                        "case_id": "quick_analysis",
                        "analysis_type": f"image_analysis_{analysis_type}",
                        "timestamp": datetime.now().isoformat(),
                        "image_file": filename
                    }
                    
                    rag_system.add_documents([result["analysis"]], [rag_metadata])
                    logger.info(f"✅ Análisis rápido {analysis_type} agregado al RAG")
                
                return jsonify({
                    "success": True,
                    "case_id": case_id,
                    "analysis": result,
                    "quick_analysis": case_id is None  # Indicador de análisis rápido
                })
                
            finally:
                # Limpiar archivo temporal
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            logger.error(f"❌ Error analizando imagen: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/extract_metadata', methods=['POST'])
    def extract_file_metadata():
        """Extraer metadatos de archivo subido"""
        try:
            # Verificar si se subió archivo
            if 'file' not in request.files:
                return jsonify({
                    "success": False,
                    "error": "No se encontró archivo"
                }), 400
            
            file = request.files['file']
            session_id = get_session_id()
            case_id = case_manager.get_active_case(session_id)
            
            if file.filename == '':
                return jsonify({
                    "success": False,
                    "error": "No se seleccionó archivo"
                }), 400
            
            # Guardar archivo temporal
            filename = secure_filename(file.filename)
            temp_path = f"data/temp_{filename}"
            file.save(temp_path)
            
            try:
                # Extraer metadatos
                metadata_result = metadata_extractor.extract_metadata(temp_path, case_id)
                
                # Generar resumen legible
                summary = metadata_extractor.get_summary(metadata_result)
                metadata_result["summary"] = summary
                
                # Guardar resultado en caso si está activo
                if case_id and metadata_result.get("success"):
                    case_manager.save_analysis_result(case_id, "metadata_extraction", metadata_result)
                    
                    # Agregar al RAG para futuras consultas
                    rag_metadata = {
                        "case_id": case_id,
                        "analysis_type": "metadata_extraction",
                        "timestamp": datetime.now().isoformat(),
                        "file_name": filename
                    }
                    
                    rag_system.add_documents([summary], [rag_metadata])
                    logger.info(f"✅ Metadatos agregados al RAG para caso {case_id}")
                
                return jsonify({
                    "success": True,
                    "case_id": case_id,
                    "metadata": metadata_result,
                    "filename": filename
                })
                
            finally:
                # Limpiar archivo temporal
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            logger.error(f"❌ Error extrayendo metadatos: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    logger.info("🚀 Iniciando LimitLess OSINT Tool con LangChain RAG")
    app.run(host='0.0.0.0', port=5000, debug=settings.FLASK_DEBUG) 