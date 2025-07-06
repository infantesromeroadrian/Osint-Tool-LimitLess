import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Settings:
    """
    Configuración simplificada para LimitLess OSINT Tool con LangChain RAG
    """
    
    # === FLASK ===
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'limitless-osint-secret-key')
    FLASK_DEBUG: bool = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # === OPENAI ===
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-4.1')
    OPENAI_VISION_MODEL: str = os.getenv('OPENAI_VISION_MODEL', 'gpt-4.1')
    
    # === RAG con LangChain ===
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.3
    
    # === VECTOR STORE ===
    CHROMA_DB_PATH: str = './data/chroma_db'

# Instancia global
settings = Settings() 