"""
LimitLess OSINT Tool - Aplicación Principal
Versión refactorizada y optimizada
"""

import logging
import os
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from flask import Flask, render_template, request, jsonify, session
    from werkzeug.utils import secure_filename
    FLASK_AVAILABLE = True
except ImportError:
    logger.error("❌ Flask no está disponible. Ejecutar: pip install flask")
    FLASK_AVAILABLE = False

# Configuración
from src.config.settings import settings

# Módulos principales
from src.modules.rag.langchain_rag import get_rag_system
from src.modules.vision.image_analyzer import image_analyzer
from src.modules.cases.case_manager import case_manager
from src.modules.metadata.extractor import modular_extractor as metadata_extractor
from src.modules.conversation_manager import conversation_manager
from src.modules.transcription.transcriber import get_audio_transcriber

def create_app():
    """Crear aplicación Flask simplificada"""
    if not FLASK_AVAILABLE:
        logger.error("❌ No se puede crear la aplicación: Flask no disponible")
        return None
    
    app = Flask(__name__)
    app.secret_key = settings.SECRET_KEY
    
    def get_session_id():
        """Obtener o crear session ID"""
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        return session['session_id']
    
    # ==================== RUTAS PRINCIPALES ====================
    
    @app.route('/')
    def index():
        """Página principal"""
        return render_template('index.html')
    
    @app.route('/chat', methods=['POST'])
    def chat():
        """Chat conversacional simplificado"""
        try:
            data = request.get_json()
            message = data.get('message', '').strip()
            
            if not message:
                return jsonify({"success": False, "error": "Mensaje requerido"}), 400
            
            session_id = get_session_id()
            case_id = case_manager.get_active_case(session_id)
            
            # Agregar mensaje del usuario
            conversation_manager.add_message(session_id, "user", message)
            
            # Obtener contexto
            conversation_context = conversation_manager.get_conversation_context(session_id, max_messages=8)
            
            # Contexto del caso
            case_context = ""
            if case_id:
                case_data = case_manager.get_case_metadata(case_id)
                if case_data:
                    case_context = f"Caso activo: {case_data.get('title', case_id)}"
            
            # Crear pregunta enriquecida
            enriched_question = message
            if conversation_context:
                enriched_question = f"Contexto: {conversation_context}\n\nPregunta: {message}"
            
            # Ejecutar consulta RAG
            result = get_rag_system().query(enriched_question)
            
            # Agregar respuesta
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
            
            # Obtener conversación completa
            full_conversation = conversation_manager.get_conversation(session_id)
            
            # Generar sugerencias
            suggestions = conversation_manager.generate_suggestions(session_id, result["answer"])
            
            return jsonify({
                "success": True,
                "result": result,
                "conversation": full_conversation,
                "case_context": case_context,
                "suggestions": suggestions
            })
            
        except Exception as e:
            logger.error(f"❌ Error en chat: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/analyze_image', methods=['POST'])
    def analyze_image():
        """Análisis de imagen simplificado"""
        try:
            if 'image' not in request.files:
                return jsonify({"success": False, "error": "No se encontró archivo"}), 400
            
            file = request.files['image']
            if file.filename == '':
                return jsonify({"success": False, "error": "No se seleccionó archivo"}), 400
            
            session_id = get_session_id()
            case_id = case_manager.get_active_case(session_id)
            analysis_type = request.form.get('analysis_type', 'general')
            
            # Guardar archivo temporal
            filename = secure_filename(file.filename)
            temp_path = f"data/temp_{filename}"
            file.save(temp_path)
            
            try:
                # Contexto del caso
                case_context = ""
                if case_id:
                    case_data = case_manager.get_case_metadata(case_id)
                    if case_data:
                        case_context = f"Caso: {case_data.get('title', case_id)}"
                
                if not case_context:
                    case_context = f"Análisis rápido de imagen: {filename}"
                
                # Analizar imagen
                result = image_analyzer.analyze_image(temp_path, case_context, analysis_type)
                
                # Extraer metadatos
                metadata_result = metadata_extractor.extract_metadata(temp_path, case_id)
                result["metadata"] = metadata_result
                
                # Guardar en caso si está activo
                if result.get("success") and case_id:
                    case_manager.save_analysis_result(case_id, "image_analysis", result)
                    
                    # Agregar al RAG
                    rag_metadata = {
                        "case_id": case_id,
                        "analysis_type": f"image_analysis_{analysis_type}",
                        "timestamp": datetime.now().isoformat(),
                        "image_file": filename
                    }
                    
                    get_rag_system().add_documents([result["analysis"]], [rag_metadata])
                    logger.info(f"✅ Análisis {analysis_type} agregado al RAG")
                
                return jsonify({
                    "success": True,
                    "case_id": case_id,
                    "analysis": result,
                    "quick_analysis": case_id is None
                })
                
            finally:
                # Limpiar archivo temporal
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
        except Exception as e:
            logger.error(f"❌ Error analizando imagen: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/extract_metadata', methods=['POST'])
    def extract_metadata():
        """Extracción de metadatos simplificada"""
        try:
            if 'file' not in request.files:
                return jsonify({"success": False, "error": "No se encontró archivo"}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({"success": False, "error": "No se seleccionó archivo"}), 400
            
            session_id = get_session_id()
            case_id = case_manager.get_active_case(session_id)
            
            # Guardar archivo temporal
            filename = secure_filename(file.filename)
            temp_path = f"data/temp_{filename}"
            file.save(temp_path)
            
            try:
                # Extraer metadatos
                metadata_result = metadata_extractor.extract_metadata(temp_path, case_id)
                
                # Generar resumen
                summary = metadata_extractor.get_summary(metadata_result)
                metadata_result["summary"] = summary
                
                # Guardar en caso si está activo
                if case_id and metadata_result.get("success"):
                    case_manager.save_analysis_result(case_id, "metadata_extraction", metadata_result)
                    
                    # Agregar al RAG
                    rag_metadata = {
                        "case_id": case_id,
                        "analysis_type": "metadata_extraction",
                        "timestamp": datetime.now().isoformat(),
                        "file_name": filename
                    }
                    
                    get_rag_system().add_documents([summary], [rag_metadata])
                    logger.info(f"✅ Metadatos agregados al RAG")
                
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
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/transcribe', methods=['POST'])
    def transcribe_audio():
        """Transcripción de audio y procesamiento RAG"""
        try:
            if 'audio' not in request.files:
                return jsonify({"success": False, "error": "No se encontró archivo de audio"}), 400
            
            file = request.files['audio']
            if file.filename == '':
                return jsonify({"success": False, "error": "No se seleccionó archivo"}), 400
            
            session_id = get_session_id()
            case_id = case_manager.get_active_case(session_id)
            
            # Parámetros de transcripción
            model_size = request.form.get('model_size', 'base')
            language = request.form.get('language', None)
            initial_prompt = request.form.get('initial_prompt', None)
            vad_filter = request.form.get('vad_filter', 'true').lower() == 'true'
            word_timestamps = request.form.get('word_timestamps', 'false').lower() == 'true'
            beam_size = int(request.form.get('beam_size', 5))
            
            # Validar modelo
            transcriber = get_audio_transcriber()
            available_models = transcriber.get_available_models()
            if model_size not in available_models:
                return jsonify({
                    "success": False, 
                    "error": f"Modelo no válido. Disponibles: {available_models}"
                }), 400
            
            logger.info(f"🎵 Iniciando transcripción con modelo {model_size}")
            
            # Leer bytes del archivo
            audio_bytes = file.read()
            filename = secure_filename(file.filename)
            
            # Transcribir audio
            result = transcriber.transcribe_bytes(
                audio_bytes=audio_bytes,
                filename=filename,
                model_size=model_size,
                language=language,
                initial_prompt=initial_prompt,
                vad_filter=vad_filter,
                word_timestamps=word_timestamps,
                beam_size=beam_size
            )
            
            if result["success"]:
                transcript = result["transcript"]
                
                # Procesar con RAG si hay transcripción
                if transcript.strip():
                    # Contexto del caso
                    case_context = ""
                    if case_id:
                        case_data = case_manager.get_case_metadata(case_id)
                        if case_data:
                            case_context = f"Caso: {case_data.get('title', case_id)}"
                    
                    # Guardar en caso si está activo
                    if case_id:
                        case_manager.save_analysis_result(case_id, "audio_transcription", result)
                        
                        # Agregar al RAG
                        rag_metadata = {
                            "case_id": case_id,
                            "analysis_type": "audio_transcription",
                            "timestamp": datetime.now().isoformat(),
                            "file_name": filename,
                            "language": result["metadata"].get("language"),
                            "duration": result["metadata"].get("duration"),
                            "model_size": model_size
                        }
                        
                        # Agregar transcripción al RAG
                        get_rag_system().add_documents([transcript], [rag_metadata])
                        logger.info(f"✅ Transcripción agregada al RAG")
                        
                        # Agregar mensaje a la conversación
                        conversation_manager.add_message(
                            session_id, 
                            "system", 
                            f"📝 Audio transcrito: {filename}",
                            metadata={
                                "type": "transcription",
                                "language": result["metadata"].get("language"),
                                "duration": result["metadata"].get("duration"),
                                "case_id": case_id
                            }
                        )
                
                return jsonify({
                    "success": True,
                    "case_id": case_id,
                    "transcription": result,
                    "filename": filename,
                    "added_to_rag": transcript.strip() != ""
                })
                
            else:
                return jsonify(result), 500
                
        except Exception as e:
            logger.error(f"❌ Error en transcripción: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/transcribe/info', methods=['GET'])
    def transcribe_info():
        """Información sobre el sistema de transcripción"""
        try:
            transcriber = get_audio_transcriber()
            system_info = transcriber.get_system_info()
            return jsonify({
                "success": True,
                "system_info": system_info
            })
        except Exception as e:
            logger.error(f"❌ Error obteniendo info de transcripción: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/process_text', methods=['POST'])
    def process_text():
        """Procesar texto y añadir al sistema RAG"""
        try:
            data = request.get_json()
            text = data.get('text', '').strip()
            
            if not text:
                return jsonify({"success": False, "error": "Texto requerido"}), 400
            
            session_id = get_session_id()
            case_id = case_manager.get_active_case(session_id)
            
            # Preparar metadata
            rag_metadata = {
                "timestamp": datetime.now().isoformat(),
                "source": "manual_input",
                "session_id": session_id
            }
            
            # Añadir caso si está activo
            if case_id:
                case_data = case_manager.get_case_metadata(case_id)
                rag_metadata["case_id"] = case_id
                if case_data:
                    rag_metadata["case_title"] = case_data.get('title', case_id)
                
                # Guardar en caso
                case_manager.save_analysis_result(case_id, "manual_text_input", {
                    "text": text,
                    "timestamp": datetime.now().isoformat(),
                    "source": "manual_input"
                })
            
            # Agregar al RAG
            success = get_rag_system().add_documents([text], [rag_metadata])
            
            if success:
                logger.info(f"✅ Texto agregado al RAG: {text[:100]}...")
                return jsonify({
                    "success": True,
                    "message": "Texto agregado al sistema RAG",
                    "case_id": case_id,
                    "text_length": len(text)
                })
            else:
                return jsonify({"success": False, "error": "Error agregando texto al RAG"}), 500
                
        except Exception as e:
            logger.error(f"❌ Error procesando texto: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    # ==================== RUTAS DE CASOS ====================
    
    @app.route('/cases', methods=['GET'])
    def get_cases():
        """Obtener lista de casos"""
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
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/cases', methods=['POST'])
    def create_case():
        """Crear nuevo caso"""
        try:
            data = request.get_json()
            title = data.get('title', '').strip()
            description = data.get('description', '').strip()
            case_type = data.get('case_type', 'intelligence')
            
            if not title:
                return jsonify({"success": False, "error": "Título requerido"}), 400
            
            # Crear caso
            result = case_manager.create_case(title, description, case_type)
            
            if result["success"]:
                # Activar automáticamente
                session_id = get_session_id()
                case_manager.set_active_case(session_id, result["case_id"])
                logger.info(f"✅ Caso creado: {result['case_id']}")
                
            return jsonify(result)
                
        except Exception as e:
            logger.error(f"❌ Error creando caso: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/cases/<case_id>/activate', methods=['POST'])
    def activate_case(case_id):
        """Activar caso"""
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
                return jsonify({"success": False, "error": "Caso no encontrado"}), 404
                
        except Exception as e:
            logger.error(f"❌ Error activando caso: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    # ==================== RUTAS DE UTILIDAD ====================
    
    @app.route('/chat/clear', methods=['POST'])
    def clear_chat():
        """Limpiar conversación"""
        try:
            session_id = get_session_id()
            conversation_manager.clear_conversation(session_id)
            return jsonify({"success": True, "message": "Conversación limpiada"})
        except Exception as e:
            logger.error(f"❌ Error limpiando chat: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/stats')
    def get_stats():
        """Estadísticas del sistema"""
        try:
            stats = get_rag_system().get_stats()
            return jsonify({"success": True, "stats": stats})
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    if app:
        logger.info("🚀 Iniciando LimitLess OSINT Tool")
        app.run(host='0.0.0.0', port=5000, debug=settings.FLASK_DEBUG)
    else:
        logger.error("❌ No se pudo iniciar la aplicación") 