"""
LangChain RAG System - Implementación moderna con LangChain 0.2.x
Siguiendo documentación oficial actualizada y mejores prácticas
INCLUYE MEMORIA CONVERSACIONAL COMPLETA
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Deshabilitar telemetría de ChromaDB
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"

# LangChain 0.2.x imports modernos
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
# TODO: Cambiar a langchain_chroma cuando esté disponible
from langchain_community.vectorstores import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

# Memoria conversacional
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Configuración
from src.config.settings import settings

logger = logging.getLogger(__name__)

class LangChainRAG:
    """
    Sistema RAG usando LangChain 0.2.x con API moderna
    Implementación actualizada siguiendo mejores prácticas oficiales:
    - Usa create_retrieval_chain y create_stuff_documents_chain
    - Maneja errores con sistema fallback
    - Implementa lazy loading para mejor rendimiento
    - INCLUYE MEMORIA CONVERSACIONAL COMPLETA POR SESIÓN
    """
    
    def __init__(self):
        """Inicializar sistema RAG con LangChain 0.2.x API moderna y memoria conversacional"""
        try:
            # Validar API key
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY requerida")
            
            # Configurar embeddings (nueva sintaxis)
            os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
            self.embeddings = OpenAIEmbeddings()
            
            # Configurar text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
                length_function=len,
            )
            
            # Configurar LLM (nueva sintaxis ChatOpenAI)
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.3
            )
            
            # Inicializar vector store
            self.vector_store = None
            self._init_vector_store()
            
            # Inicializar memoria conversacional
            self.message_histories: Dict[str, BaseChatMessageHistory] = {}
            
            # Crear RAG chain con memoria conversacional
            self.qa_chain = None
            self._create_conversational_qa_chain()
            
            logger.info("✅ LangChain RAG 0.2.x inicializado correctamente con API moderna y memoria conversacional")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando LangChain RAG: {e}")
            raise

    def _init_vector_store(self):
        """Inicializar Chroma vector store"""
        try:
            # Crear directorio si no existe
            os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
            
            # Inicializar Chroma (nueva sintaxis)
            self.vector_store = Chroma(
                embedding_function=self.embeddings,
                persist_directory=settings.CHROMA_DB_PATH
            )
            
            # Verificar que el vector store se inicializó correctamente
            if self.vector_store is None:
                raise ValueError("Vector store no se pudo inicializar")
            
            logger.info(f"📊 Vector store inicializado: {settings.CHROMA_DB_PATH}")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando vector store: {e}")
            self.vector_store = None
            raise

    def _get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Obtener o crear historial de mensajes para una sesión"""
        if session_id not in self.message_histories:
            self.message_histories[session_id] = ChatMessageHistory()
            logger.info(f"🆕 Nueva sesión de memoria creada: {session_id}")
        return self.message_histories[session_id]

    def _create_conversational_qa_chain(self):
        """Crear cadena de Q&A conversacional con retrieval usando la API moderna"""
        try:
            if self.vector_store is None:
                raise ValueError("Vector store no inicializado")
            
            # Crear retriever
            retriever = self.vector_store.as_retriever(
                search_kwargs={
                    "k": settings.TOP_K_RESULTS
                }
            )
            
            # Crear prompt conversacional para RAG
            system_prompt = (
                "Eres un asistente especializado en análisis OSINT e inteligencia. "
                "Usa la siguiente información recuperada del contexto para responder "
                "la pregunta del usuario. Si no conoces la respuesta basándote en el "
                "contexto proporcionado, di claramente que no lo sabes. "
                "Mantén las respuestas concisas y precisas.\n"
                "Si te han dado información sobre intentos previos fallidos (como aliases probados), "
                "toma esa información en cuenta para no repetir sugerencias.\n\n"
                "Contexto recuperado:\n{context}"
            )
            
            # Prompt con memoria conversacional
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ])
            
            # Crear chain de documentos
            question_answer_chain = create_stuff_documents_chain(
                self.llm, 
                prompt,
                output_parser=StrOutputParser()
            )
            
            # Crear chain de retrieval completa
            rag_chain = create_retrieval_chain(
                retriever, 
                question_answer_chain
            )
            
            # Envolver con memoria conversacional
            self.qa_chain = RunnableWithMessageHistory(
                rag_chain,
                self._get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
                output_messages_key="answer"
            )
            
            logger.info("🔗 QA Chain conversacional creada correctamente con API moderna")
            
        except Exception as e:
            logger.error(f"❌ Error creando QA chain conversacional: {e}")
            raise

    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict]] = None) -> bool:
        """Agregar documentos al vector store"""
        try:
            if not texts:
                logger.warning("⚠️ No hay textos para agregar")
                return False
            
            # Crear documentos
            documents = []
            for i, text in enumerate(texts):
                metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
                doc = Document(
                    page_content=text,
                    metadata=metadata
                )
                documents.append(doc)
            
            # Dividir en chunks
            chunks = self.text_splitter.split_documents(documents)
            
            # Agregar al vector store
            if self.vector_store is not None:
                self.vector_store.add_documents(chunks)
            
            logger.info(f"📄 {len(chunks)} chunks agregados al vector store")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error agregando documentos: {e}")
            return False

    def query(self, question: str, session_id: str = "default") -> Dict[str, Any]:
        """Ejecutar consulta RAG conversacional usando la API moderna"""
        start_time = datetime.now()
        
        try:
            if not self.qa_chain:
                raise ValueError("QA Chain no inicializada")
            
            logger.info(f"🔍 Ejecutando consulta conversacional: {question} [sesión: {session_id}]")
            
            # Ejecutar consulta con memoria conversacional
            result = self.qa_chain.invoke(
                {"input": question},
                config={"configurable": {"session_id": session_id}}
            )
            
            # Extraer información con nueva estructura
            answer = result.get("answer", "No se pudo generar respuesta")
            source_docs = result.get("context", [])
            
            # Calcular tiempo
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Obtener historial de la sesión para estadísticas
            session_history = self._get_session_history(session_id)
            history_length = len(session_history.messages) if hasattr(session_history, 'messages') else 0
            
            # Preparar respuesta
            response = {
                "question": question,
                "answer": answer,
                "source_documents": [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in source_docs
                ],
                "processing_time": processing_time,
                "session_id": session_id,
                "conversation_length": history_length,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Consulta conversacional completada en {processing_time:.2f}s")
            logger.info(f"📊 Documentos fuente: {len(source_docs)} | Historial: {history_length} mensajes")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error en consulta RAG conversacional: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "question": question,
                "answer": f"Error: {str(e)}",
                "source_documents": [],
                "processing_time": processing_time,
                "session_id": session_id,
                "conversation_length": 0,
                "error": True
            }

    def clear_session_history(self, session_id: str) -> bool:
        """Limpiar historial de una sesión específica"""
        try:
            if session_id in self.message_histories:
                self.message_histories[session_id].clear()
                logger.info(f"🧹 Historial limpiado para sesión: {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error limpiando historial de sesión {session_id}: {e}")
            return False

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Obtener historial de mensajes de una sesión"""
        try:
            if session_id in self.message_histories:
                messages = self.message_histories[session_id].messages
                return [
                    {
                        "type": "human" if isinstance(msg, HumanMessage) else "ai",
                        "content": msg.content,
                        "timestamp": getattr(msg, 'timestamp', None)
                    }
                    for msg in messages
                ]
            return []
        except Exception as e:
            logger.error(f"❌ Error obteniendo historial de sesión {session_id}: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema"""
        try:
            # Información básica del sistema
            stats = {
                "vector_store_status": "inicializado" if self.vector_store else "no inicializado",
                "qa_chain_status": "inicializado" if self.qa_chain else "no inicializado",
                "chunk_size": settings.CHUNK_SIZE,
                "chunk_overlap": settings.CHUNK_OVERLAP,
                "top_k": settings.TOP_K_RESULTS,
                "similarity_threshold": settings.SIMILARITY_THRESHOLD,
                "chroma_path": settings.CHROMA_DB_PATH,
                "langchain_version": "0.2.x (API moderna)",
                "chain_type": "create_retrieval_chain",
                "memory_enabled": True,
                "active_sessions": len(self.message_histories),
                "session_ids": list(self.message_histories.keys())
            }
            
            # Estadísticas de memoria por sesión
            session_stats = {}
            for session_id, history in self.message_histories.items():
                try:
                    session_stats[session_id] = {
                        "message_count": len(history.messages) if hasattr(history, 'messages') else 0,
                        "last_activity": datetime.now().isoformat()  # Placeholder
                    }
                except:
                    session_stats[session_id] = {"message_count": 0, "last_activity": None}
            
            stats["session_statistics"] = session_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {"error": str(e)}

# Instancia global (lazy loading)
rag_system = None

def get_rag_system():
    """Obtener instancia del sistema RAG con lazy loading"""
    global rag_system
    if rag_system is None:
        try:
            rag_system = LangChainRAG()
        except Exception as e:
            logger.error(f"❌ Error inicializando sistema RAG: {e}")
            # Crear un sistema RAG dummy para que la aplicación funcione
            rag_system = DummyRAG()
    return rag_system

class DummyRAG:
    """Sistema RAG dummy para cuando hay problemas de inicialización"""
    
    def query(self, question: str, session_id: str = "default") -> Dict[str, Any]:
        """Respuesta dummy"""
        return {
            "question": question,
            "answer": "Sistema RAG no disponible. Verifica la configuración de OpenAI API Key.",
            "source_documents": [],
            "processing_time": 0.0,
            "session_id": session_id,
            "conversation_length": 0,
            "error": True
        }
    
    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict]] = None) -> bool:
        """Método dummy para agregar documentos"""
        logger.warning("⚠️ Sistema RAG no disponible - documentos no agregados")
        return False
    
    def clear_session_history(self, session_id: str) -> bool:
        """Método dummy para limpiar historial"""
        return False
        
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Método dummy para obtener historial"""
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas dummy"""
        return {
            "vector_store_status": "no disponible",
            "qa_chain_status": "no disponible",
            "memory_enabled": False,
            "active_sessions": 0,
            "error": "Sistema RAG no inicializado"
        } 