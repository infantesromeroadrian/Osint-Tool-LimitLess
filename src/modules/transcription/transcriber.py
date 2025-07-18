"""
Módulo de transcripción de audio usando faster-whisper
Implementa transcripción rápida y precisa de archivos de audio
"""

import os
import logging
import tempfile
import mimetypes
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime

try:
    from faster_whisper import WhisperModel  # type: ignore
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    WhisperModel = None  # type: ignore
    FASTER_WHISPER_AVAILABLE = False

from src.config.settings import settings

logger = logging.getLogger(__name__)

class AudioTranscriber:
    """
    Transcriptor de audio usando faster-whisper
    Optimizado para velocidad y precisión
    """
    
    def __init__(self):
        """Inicializar el transcriptor"""
        self.model: Optional[Any] = None
        self.model_size = "base"  # Modelo por defecto
        self.device = self._detect_device()
        self.compute_type = self._get_compute_type()
        self._ensure_faster_whisper()
        
    def _ensure_faster_whisper(self):
        """Verificar que faster-whisper esté disponible"""
        if not FASTER_WHISPER_AVAILABLE:
            raise ImportError(
                "faster-whisper no está disponible. "
                "Instálalo con: pip install faster-whisper"
            )
    
    def _detect_device(self) -> str:
        """Detectar dispositivo disponible (CPU/CUDA)"""
        try:
            import torch
            if torch.cuda.is_available():
                logger.info("🔥 CUDA disponible, usando GPU")
                return "cuda"
        except ImportError:
            pass
        
        logger.info("💻 Usando CPU para transcripción")
        return "cpu"
    
    def _get_compute_type(self) -> str:
        """Obtener tipo de computación según el dispositivo"""
        if self.device == "cuda":
            return "float16"  # Más rápido en GPU
        else:
            return "int8"     # Menos memoria en CPU
    
    def _load_model(self, model_size: str = "base") -> None:
        """Cargar modelo de whisper"""
        try:
            if self.model is None or self.model_size != model_size:
                logger.info(f"🔄 Cargando modelo {model_size} en {self.device}")
                
                self.model = WhisperModel(  # type: ignore
                    model_size,
                    device=self.device,
                    compute_type=self.compute_type
                )
                
                self.model_size = model_size
                logger.info(f"✅ Modelo {model_size} cargado correctamente")
                
        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {e}")
            raise
    
    def _validate_audio_file(self, file_path: str) -> bool:
        """Validar que el archivo sea de audio"""
        if not os.path.exists(file_path):
            return False
        
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type.startswith('audio/'):
            return True
        
        # Verificar extensiones comunes
        audio_extensions = {'.mp3', '.wav', '.ogg', '.flac', '.m4a', '.wma', '.aac'}
        return Path(file_path).suffix.lower() in audio_extensions
    
    def transcribe_file(
        self,
        file_path: str,
        model_size: str = "base",
        language: Optional[str] = None,
        initial_prompt: Optional[str] = None,
        vad_filter: bool = True,
        word_timestamps: bool = False,
        beam_size: int = 5
    ) -> Dict[str, Any]:
        """
        Transcribir archivo de audio
        
        Args:
            file_path: Ruta al archivo de audio
            model_size: Tamaño del modelo ('tiny', 'base', 'small', 'medium', 'large-v3')
            language: Idioma del audio (e.g., 'es', 'en')
            initial_prompt: Prompt inicial para guiar la transcripción
            vad_filter: Filtro de actividad de voz
            word_timestamps: Timestamps a nivel de palabra
            beam_size: Tamaño del haz de búsqueda
            
        Returns:
            Dict con transcripción y metadata
        """
        start_time = datetime.now()
        
        try:
            # Validar archivo
            if not self._validate_audio_file(file_path):
                return {
                    "success": False,
                    "error": "Archivo no válido o no es de audio",
                    "supported_formats": ["mp3", "wav", "ogg", "flac", "m4a", "wma", "aac"]
                }
            
            # Cargar modelo
            self._load_model(model_size)
            
            logger.info(f"🎵 Transcribiendo archivo: {file_path}")
            
            # Configurar parámetros de transcripción
            transcribe_options = {
                "beam_size": beam_size,
                "word_timestamps": word_timestamps,
                "vad_filter": vad_filter,
            }
            
            if language:
                transcribe_options["language"] = language
            
            if initial_prompt:
                transcribe_options["initial_prompt"] = initial_prompt
            
            # Ejecutar transcripción
            segments, info = self.model.transcribe(file_path, **transcribe_options)  # type: ignore
            
            # Procesar resultados
            transcript_text = ""
            segments_list = []
            
            for segment in segments:
                transcript_text += segment.text + " "
                
                segment_data = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                }
                
                # Añadir timestamps de palabras si están disponibles
                if word_timestamps and hasattr(segment, 'words'):
                    segment_data["words"] = [
                        {
                            "start": word.start,
                            "end": word.end,
                            "word": word.word
                        }
                        for word in segment.words
                    ]
                
                segments_list.append(segment_data)
            
            # Calcular tiempo de procesamiento
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Preparar respuesta
            result = {
                "success": True,
                "transcript": transcript_text.strip(),
                "segments": segments_list,
                "metadata": {
                    "language": info.language,
                    "language_probability": info.language_probability,
                    "duration": info.duration,
                    "model_size": model_size,
                    "device": self.device,
                    "compute_type": self.compute_type,
                    "processing_time": processing_time,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            logger.info(f"✅ Transcripción completada en {processing_time:.2f}s")
            logger.info(f"📊 Idioma detectado: {info.language} (probabilidad: {info.language_probability:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en transcripción: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": False,
                "error": str(e),
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }
    
    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        filename: str,
        model_size: str = "base",
        language: Optional[str] = None,
        initial_prompt: Optional[str] = None,
        vad_filter: bool = True,
        word_timestamps: bool = False,
        beam_size: int = 5
    ) -> Dict[str, Any]:
        """
        Transcribir audio desde bytes
        
        Args:
            audio_bytes: Bytes del archivo de audio
            filename: Nombre del archivo original
            model_size: Tamaño del modelo
            language: Idioma del audio
            initial_prompt: Prompt inicial
            vad_filter: Filtro de actividad de voz
            word_timestamps: Timestamps a nivel de palabra
            beam_size: Tamaño del haz de búsqueda
            
        Returns:
            Dict con transcripción y metadata
        """
        try:
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(
                suffix=Path(filename).suffix,
                delete=False
            ) as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_file.flush()
                
                # Transcribir archivo temporal
                result = self.transcribe_file(
                    tmp_file.name,
                    model_size=model_size,
                    language=language,
                    initial_prompt=initial_prompt,
                    vad_filter=vad_filter,
                    word_timestamps=word_timestamps,
                    beam_size=beam_size
                )
                
                # Añadir información del archivo original
                if result["success"]:
                    result["metadata"]["original_filename"] = filename
                
                # Limpiar archivo temporal
                try:
                    os.unlink(tmp_file.name)
                except:
                    pass
                
                return result
                
        except Exception as e:
            logger.error(f"❌ Error transcribiendo bytes: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_available_models(self) -> List[str]:
        """Obtener lista de modelos disponibles"""
        return [
            "tiny",      # ~1 GB VRAM
            "base",      # ~1 GB VRAM
            "small",     # ~2 GB VRAM
            "medium",    # ~5 GB VRAM
            "large-v3",  # ~10 GB VRAM
            "distil-large-v3"  # Modelo optimizado
        ]
    
    def get_supported_languages(self) -> List[str]:
        """Obtener lista de idiomas soportados"""
        return [
            "es", "en", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh",
            "ar", "hi", "tr", "pl", "nl", "sv", "da", "no", "fi", "cs",
            "sk", "hu", "ro", "bg", "hr", "sr", "sl", "lv", "lt", "et",
            "mt", "cy", "ga", "eu", "ca", "gl", "ast", "oc", "br", "co"
        ]
    
    def get_system_info(self) -> Dict[str, Any]:
        """Obtener información del sistema"""
        return {
            "faster_whisper_available": FASTER_WHISPER_AVAILABLE,
            "device": self.device,
            "compute_type": self.compute_type,
            "current_model": self.model_size if self.model else None,
            "available_models": self.get_available_models(),
            "supported_languages": self.get_supported_languages()
        }

# Instancia global (lazy loading)
audio_transcriber = None

def get_audio_transcriber():
    """Obtener instancia del transcriptor con lazy loading"""
    global audio_transcriber
    if audio_transcriber is None:
        if not FASTER_WHISPER_AVAILABLE:
            return DummyTranscriber()
        try:
            audio_transcriber = AudioTranscriber()
        except Exception as e:
            logger.error(f"❌ Error inicializando transcriptor: {e}")
            return DummyTranscriber()
    return audio_transcriber

class DummyTranscriber:
    """Transcriptor dummy para cuando faster-whisper no está disponible"""
    
    def transcribe_bytes(self, *args, **kwargs):
        """Respuesta dummy"""
        return {
            "success": False,
            "error": "faster-whisper no está disponible. Usar Docker para funcionalidad completa.",
            "transcript": "",
            "segments": [],
            "metadata": {}
        }
    
    def transcribe_file(self, *args, **kwargs):
        """Respuesta dummy"""
        return {
            "success": False,
            "error": "faster-whisper no está disponible. Usar Docker para funcionalidad completa.",
            "transcript": "",
            "segments": [],
            "metadata": {}
        }
    
    def get_available_models(self):
        """Modelos dummy"""
        return []
    
    def get_supported_languages(self):
        """Idiomas dummy"""
        return []
    
    def get_system_info(self):
        """Info dummy"""
        return {
            "faster_whisper_available": False,
            "device": "dummy",
            "compute_type": "dummy",
            "current_model": None,
            "available_models": [],
            "supported_languages": [],
            "error": "faster-whisper no está disponible"
        } 