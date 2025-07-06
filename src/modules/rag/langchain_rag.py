"""
LangChain RAG System - Implementación oficial con LangChain 0.2.x
Siguiendo documentación oficial actualizada
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Deshabilitar telemetría de ChromaDB
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"

# LangChain 0.2.x imports (nueva API)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.schema import Document

# Configuración
from src.config.settings import settings

logger = logging.getLogger(__name__)

class LangChainRAG:
    """
    Sistema RAG usando LangChain 0.2.x oficial
    Implementación actualizada siguiendo docs oficiales
    """
    
    def __init__(self):
        """Inicializar sistema RAG con LangChain 0.2.x"""
        try:
            # Validar API key
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY requerida")
            
            # Configurar embeddings (nueva sintaxis)
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            # Configurar text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
                length_function=len,
            )
            
            # Configurar LLM (nueva sintaxis ChatOpenAI)
            self.llm = ChatOpenAI(
                openai_api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                temperature=0.3
            )
            
            # Inicializar vector store
            self.vector_store = None
            self._init_vector_store()
            
            # Crear RAG chain
            self.qa_chain = None
            self._create_qa_chain()
            
            logger.info("✅ LangChain RAG 0.2.x inicializado correctamente")
            
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
            
            logger.info(f"📊 Vector store inicializado: {settings.CHROMA_DB_PATH}")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando vector store: {e}")
            raise

    def _create_qa_chain(self):
        """Crear cadena de Q&A con retrieval"""
        try:
            if not self.vector_store:
                raise ValueError("Vector store no inicializado")
            
            # Crear retriever
            retriever = self.vector_store.as_retriever(
                search_kwargs={
                    "k": settings.TOP_K_RESULTS
                }
            )
            
            # Crear chain de Q&A (nueva sintaxis)
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True
            )
            
            logger.info("🔗 QA Chain creada correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error creando QA chain: {e}")
            raise

    def add_documents(self, texts: List[str], metadatas: List[Dict] = None) -> bool:
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
            self.vector_store.add_documents(chunks)
            
            logger.info(f"📄 {len(chunks)} chunks agregados al vector store")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error agregando documentos: {e}")
            return False

    def query(self, question: str) -> Dict[str, Any]:
        """Ejecutar consulta RAG"""
        start_time = datetime.now()
        
        try:
            if not self.qa_chain:
                raise ValueError("QA Chain no inicializada")
            
            logger.info(f"🔍 Ejecutando consulta: {question}")
            
            # Ejecutar consulta (nueva sintaxis)
            result = self.qa_chain.invoke({"query": question})
            
            # Extraer información
            answer = result.get("result", "No se pudo generar respuesta")
            source_docs = result.get("source_documents", [])
            
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
                "langchain_version": "0.2.x"
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {"error": str(e)}

# Instancia global
rag_system = LangChainRAG() 