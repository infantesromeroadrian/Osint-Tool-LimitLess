"""
Conversation Manager - Gestor de conversaciones por sesión
Módulo separado para mantener app.py más limpio
"""

import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ConversationManager:
    """Gestor de conversaciones por sesión"""
    
    def __init__(self):
        self.conversations = {}  # session_id -> list of messages
        self.message_reactions = {}  # session_id -> {message_id: {reaction: count}}
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Agregar mensaje a la conversación"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
            "message_id": str(uuid.uuid4()),
            "reactions": {}
        }
        
        self.conversations[session_id].append(message)
        
        # Mantener solo los últimos 20 mensajes
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
                    
                    # Toggle reaction
                    if reaction in message["reactions"]:
                        message["reactions"][reaction] += 1
                    else:
                        message["reactions"][reaction] = 1
                    
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ Error adding reaction: {e}")
            return False
    
    def get_conversation(self, session_id: str) -> List[Dict[str, Any]]:
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
    
    def generate_suggestions(self, session_id: str, latest_content: str, analysis_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generar sugerencias proactivas basadas en contexto"""
        suggestions = []
        
        try:
            content_lower = latest_content.lower()
            
            # Sugerencias basadas en contenido
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
            
            # Sugerencias basadas en tipo de análisis
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
            
            # Sugerencias contextuales generales
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

# Instancia global
conversation_manager = ConversationManager() 