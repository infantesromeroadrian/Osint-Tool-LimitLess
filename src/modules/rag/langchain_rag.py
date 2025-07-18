"""
LangChain RAG System - Implementación moderna con LangChain 0.2.x
Siguiendo documentación oficial actualizada y mejores prácticas
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
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

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
    """
    
    def __init__(self):
        """Inicializar sistema RAG con LangChain 0.2.x API moderna"""
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
            
            # Crear RAG chain
            self.qa_chain = None
            self._create_qa_chain()
            
            logger.info("✅ LangChain RAG 0.2.x inicializado correctamente con API moderna")
            
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

    def _create_qa_chain(self):
        """Crear cadena de Q&A con retrieval usando la API moderna"""
        try:
            if self.vector_store is None:
                raise ValueError("Vector store no inicializado")
            
            # Crear retriever
            retriever = self.vector_store.as_retriever(
                search_kwargs={
                    "k": settings.TOP_K_RESULTS
                }
            )
            
            # Crear prompt para RAG
            system_prompt = (
                "You are an assistant for question-answering tasks. "
                "Use the following pieces of retrieved context to answer "
                "the question. If you don't know the answer, say that you "
                "don't know. Use three sentences maximum and keep the "
                "answer concise."
                "\n\n"
                "{context}"
            )
            
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    ("human", "{input}"),
                ]
            )
            
            # Crear chain de documentos
            question_answer_chain = create_stuff_documents_chain(
                self.llm, 
                prompt,
                output_parser=StrOutputParser()
            )
            
            # Crear chain de retrieval completa
            self.qa_chain = create_retrieval_chain(
                retriever, 
                question_answer_chain
            )
            
            logger.info("🔗 QA Chain creada correctamente con API moderna")
            
        except Exception as e:
            logger.error(f"❌ Error creando QA chain: {e}")
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

    def query(self, question: str) -> Dict[str, Any]:
        """Ejecutar consulta RAG usando la API moderna"""
        start_time = datetime.now()
        
        try:
            if not self.qa_chain:
                raise ValueError("QA Chain no inicializada")
            
            logger.info(f"🔍 Ejecutando consulta: {question}")
            
            # Ejecutar consulta (API moderna)
            result = self.qa_chain.invoke({"input": question})
            
            # Extraer información con nueva estructura
            answer = result.get("answer", "No se pudo generar respuesta")
            source_docs = result.get("context", [])
            
            # Calcular tiempo
            processing_time = (datetime.now() - start_time).total_seconds()
            
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
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Consulta completada en {processing_time:.2f}s")
            logger.info(f"📊 Documentos fuente: {len(source_docs)}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error en consulta RAG: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "question": question,
                "answer": f"Error: {str(e)}",
                "source_documents": [],
                "processing_time": processing_time,
                "error": True
            }

    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema"""
        try:
            # Información básica del sistema
            return {
                "vector_store_status": "inicializado" if self.vector_store else "no inicializado",
                "qa_chain_status": "inicializado" if self.qa_chain else "no inicializado",
                "chunk_size": settings.CHUNK_SIZE,
                "chunk_overlap": settings.CHUNK_OVERLAP,
                "top_k": settings.TOP_K_RESULTS,
                "similarity_threshold": settings.SIMILARITY_THRESHOLD,
                "chroma_path": settings.CHROMA_DB_PATH,
                "langchain_version": "0.2.x (API moderna)",
                "chain_type": "create_retrieval_chain"
            }
            
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
    
    def query(self, question: str) -> Dict[str, Any]:
        """Respuesta dummy"""
        return {
            "question": question,
            "answer": "Sistema RAG no disponible. Verifica la configuración de OpenAI API Key.",
            "source_documents": [],
            "processing_time": 0.0,
            "error": True
        }
    
    def add_documents(self, texts: List[str], metadatas: Optional[List[Dict]] = None) -> bool:
        """Método dummy para agregar documentos"""
        logger.warning("⚠️ Sistema RAG no disponible - documentos no agregados")
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas dummy"""
        return {
            "vector_store_status": "no disponible",
            "qa_chain_status": "no disponible",
            "error": "Sistema RAG no inicializado"
        } 