"""
File Metadata Extractor
Extracción simple de metadatos para análisis forense
"""

import os
import logging
import subprocess
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import mimetypes

# Importaciones condicionales para metadatos específicos
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Verificar disponibilidad de FFmpeg
def check_ffmpeg_available():
    """Verificar si ffprobe está disponible"""
    try:
        subprocess.run(['ffprobe', '-version'], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

FFMPEG_AVAILABLE = check_ffmpeg_available()

logger = logging.getLogger(__name__)

class FileMetadataExtractor:
    """
    Extractor simple de metadatos de archivos
    Modular y especializado por tipo de archivo
    """
    
    def __init__(self):
        """Inicializar extractor de metadatos"""
        self.supported_types = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
            'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
            'video': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']
        }
        
        # Logging de capacidades
        capabilities = []
        if PIL_AVAILABLE:
            capabilities.append("PIL/Pillow (imágenes)")
        if FFMPEG_AVAILABLE:
            capabilities.append("FFmpeg (videos/audio)")
        
        logger.info(f"✅ File Metadata Extractor inicializado - Capacidades: {', '.join(capabilities) if capabilities else 'Básico'}")

    def extract_metadata(self, file_path: str, case_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Extraer metadatos completos de un archivo
        
        Args:
            file_path: Ruta del archivo
            case_id: ID del caso para contexto
            
        Returns:
            Dict con metadatos extraídos
        """
        try:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                return {"error": "File not found", "success": False}
            
            # Metadatos básicos del sistema
            basic_metadata = self._extract_basic_metadata(file_path_obj)
            
            # Metadatos específicos por tipo
            specific_metadata = self._extract_specific_metadata(file_path_obj)
            
            # Combinar resultados
            result = {
                "file_path": str(file_path_obj),
                "case_id": case_id,
                "basic": basic_metadata,
                "specific": specific_metadata,
                "extraction_timestamp": datetime.now().isoformat(),
                "success": True
            }
            
            logger.info(f"✅ Metadatos extraídos: {file_path_obj.name}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo metadatos: {e}")
            return {
                "error": str(e),
                "file_path": file_path,
                "success": False
            }

    def _extract_basic_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extraer metadatos básicos del sistema de archivos"""
        try:
            stat = file_path.stat()
            
            # Detectar tipo MIME
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            return {
                "filename": file_path.name,
                "extension": file_path.suffix.lower(),
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "mime_type": mime_type,
                "file_type": self._get_file_category(file_path.suffix.lower()),
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed_time": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:]
            }
            
        except Exception as e:
            logger.error(f"❌ Error en metadatos básicos: {e}")
            return {"error": str(e)}

    def _extract_specific_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extraer metadatos específicos según el tipo de archivo"""
        try:
            extension = file_path.suffix.lower()
            file_type = self._get_file_category(extension)
            
            if file_type == 'image':
                return self._extract_image_metadata(file_path)
            elif file_type == 'document':
                return self._extract_document_metadata(file_path)
            elif file_type == 'video':
                return self._extract_video_metadata(file_path)
            elif file_type == 'audio':
                return self._extract_audio_metadata(file_path)
            else:
                return {"type": "unknown", "details": "No specific metadata extractor available"}
                
        except Exception as e:
            logger.error(f"❌ Error en metadatos específicos: {e}")
            return {"error": str(e)}

    def _extract_image_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extraer metadatos EXIF de imágenes"""
        if not PIL_AVAILABLE:
            return {"error": "PIL not available for image metadata"}
        
        try:
            with Image.open(file_path) as img:
                # Información básica de la imagen
                basic_info = {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                }
                
                # Metadatos EXIF
                exif_data = {}
                try:
                    exif = img.getexif()
                    if exif:
                        for tag_id, value in exif.items():
                            tag = TAGS.get(tag_id, tag_id)
                            exif_data[tag] = str(value)
                except AttributeError:
                    # Fallback para versiones antiguas de PIL
                    pass
                
                return {
                    "type": "image",
                    "image_info": basic_info,
                    "exif": exif_data,
                    "color_palette": self._get_dominant_colors(img)
                }
                
        except Exception as e:
            logger.error(f"❌ Error en metadatos de imagen: {e}")
            return {"type": "image", "error": str(e)}

    def _extract_document_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extraer metadatos de documentos"""
        try:
            # Para documentos básicos, extraer información del archivo
            return {
                "type": "document",
                "encoding": self._detect_encoding(file_path) if file_path.suffix == '.txt' else "unknown",
                "line_count": self._count_lines(file_path) if file_path.suffix == '.txt' else None,
                "details": "Basic document metadata only"
            }
            
        except Exception as e:
            logger.error(f"❌ Error en metadatos de documento: {e}")
            return {"type": "document", "error": str(e)}

    def _extract_video_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extraer metadatos de videos usando ffprobe"""
        if not FFMPEG_AVAILABLE:
            return {
                "type": "video",
                "error": "FFmpeg not available",
                "note": "Install FFmpeg to extract video metadata"
            }
        
        try:
            # Ejecutar ffprobe para extraer metadatos
            cmd = [
                "ffprobe", "-v", "error", "-print_format", "json",
                "-show_format", "-show_streams", str(file_path)
            ]
            
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                return {
                    "type": "video",
                    "error": f"FFprobe error: {result.stderr}",
                    "note": "Failed to extract video metadata"
                }
            
            metadata = json.loads(result.stdout)
            
            # Extraer información del formato
            format_info = metadata.get("format", {})
            streams = metadata.get("streams", [])
            
            # Separar streams de video, audio y subtítulos
            video_streams = [s for s in streams if s.get("codec_type") == "video"]
            audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
            
            # Información principal del video
            video_info = {}
            if video_streams:
                video_stream = video_streams[0]  # Stream principal
                video_info = {
                    "codec": video_stream.get("codec_name"),
                    "width": video_stream.get("width"),
                    "height": video_stream.get("height"),
                    "aspect_ratio": video_stream.get("display_aspect_ratio"),
                    "frame_rate": video_stream.get("r_frame_rate"),
                    "bit_rate": video_stream.get("bit_rate"),
                    "pixel_format": video_stream.get("pix_fmt"),
                    "duration": video_stream.get("duration")
                }
            
            # Información de audio
            audio_info = {}
            if audio_streams:
                audio_stream = audio_streams[0]  # Stream principal
                audio_info = {
                    "codec": audio_stream.get("codec_name"),
                    "sample_rate": audio_stream.get("sample_rate"),
                    "channels": audio_stream.get("channels"),
                    "bit_rate": audio_stream.get("bit_rate"),
                    "duration": audio_stream.get("duration")
                }
            
            # Metadatos del formato/contenedor
            format_metadata = {
                "format_name": format_info.get("format_name"),
                "format_long_name": format_info.get("format_long_name"),
                "duration": format_info.get("duration"),
                "size": format_info.get("size"),
                "bit_rate": format_info.get("bit_rate"),
                "nb_streams": format_info.get("nb_streams"),
                "nb_programs": format_info.get("nb_programs")
            }
            
            # Tags/metadatos adicionales
            tags = format_info.get("tags", {})
            
            # Procesar fechas si están disponibles
            creation_date = None
            if "creation_time" in tags:
                creation_date = tags["creation_time"]
            elif "date" in tags:
                creation_date = tags["date"]
            
            return {
                "type": "video",
                "format": format_metadata,
                "video_info": video_info,
                "audio_info": audio_info,
                "creation_date": creation_date,
                "tags": tags,
                "streams_count": {
                    "video": len(video_streams),
                    "audio": len(audio_streams),
                    "total": len(streams)
                },
                "raw_metadata": metadata  # Para debugging
            }
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo metadatos de video: {e}")
            return {
                "type": "video",
                "error": str(e),
                "note": "Failed to extract video metadata"
            }

    def _extract_audio_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extraer metadatos de audio usando ffprobe"""
        if not FFMPEG_AVAILABLE:
            return {
                "type": "audio",
                "error": "FFmpeg not available",
                "note": "Install FFmpeg to extract audio metadata"
            }
        
        try:
            # Ejecutar ffprobe para extraer metadatos
            cmd = [
                "ffprobe", "-v", "error", "-print_format", "json",
                "-show_format", "-show_streams", str(file_path)
            ]
            
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                return {
                    "type": "audio",
                    "error": f"FFprobe error: {result.stderr}",
                    "note": "Failed to extract audio metadata"
                }
            
            metadata = json.loads(result.stdout)
            
            # Extraer información del formato
            format_info = metadata.get("format", {})
            streams = metadata.get("streams", [])
            
            # Información principal del audio
            audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
            
            audio_info = {}
            if audio_streams:
                audio_stream = audio_streams[0]  # Stream principal
                audio_info = {
                    "codec": audio_stream.get("codec_name"),
                    "sample_rate": audio_stream.get("sample_rate"),
                    "channels": audio_stream.get("channels"),
                    "channel_layout": audio_stream.get("channel_layout"),
                    "bit_rate": audio_stream.get("bit_rate"),
                    "duration": audio_stream.get("duration"),
                    "bits_per_sample": audio_stream.get("bits_per_raw_sample")
                }
            
            # Metadatos del formato
            format_metadata = {
                "format_name": format_info.get("format_name"),
                "format_long_name": format_info.get("format_long_name"),
                "duration": format_info.get("duration"),
                "size": format_info.get("size"),
                "bit_rate": format_info.get("bit_rate")
            }
            
            # Tags/metadatos adicionales (ID3, etc.)
            tags = format_info.get("tags", {})
            
            # Información de ID3 común
            id3_info = {
                "title": tags.get("title") or tags.get("TIT2"),
                "artist": tags.get("artist") or tags.get("TPE1"),
                "album": tags.get("album") or tags.get("TALB"),
                "date": tags.get("date") or tags.get("TYER"),
                "genre": tags.get("genre") or tags.get("TCON"),
                "track": tags.get("track") or tags.get("TRCK")
            }
            
            return {
                "type": "audio",
                "format": format_metadata,
                "audio_info": audio_info,
                "id3_tags": id3_info,
                "all_tags": tags,
                "streams_count": len(audio_streams),
                "raw_metadata": metadata  # Para debugging
            }
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo metadatos de audio: {e}")
            return {
                "type": "audio",
                "error": str(e),
                "note": "Failed to extract audio metadata"
            }

    def _get_file_category(self, extension: str) -> str:
        """Determinar categoría del archivo por extensión"""
        for category, extensions in self.supported_types.items():
            if extension in extensions:
                return category
        return "unknown"

    def _get_dominant_colors(self, img: Image.Image, num_colors: int = 5) -> list:
        """Extraer colores dominantes de una imagen"""
        try:
            # Redimensionar para análisis más rápido
            img_small = img.resize((50, 50))
            colors = img_small.getcolors(maxcolors=256)
            
            if colors:
                # Ordenar por frecuencia y tomar los más comunes
                sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)
                dominant = []
                
                for count, color in sorted_colors[:num_colors]:
                    if isinstance(color, tuple):
                        # Convertir a hex si es RGB
                        if len(color) >= 3:
                            hex_color = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                            dominant.append({"color": hex_color, "frequency": count})
                
                return dominant
            
        except Exception as e:
            logger.error(f"❌ Error analizando colores: {e}")
        
        return []

    def _detect_encoding(self, file_path: Path) -> str:
        """Detectar codificación de archivos de texto"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(1024)
                
            # Intentar detectar codificación común
            encodings = ['utf-8', 'ascii', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    raw_data.decode(encoding)
                    return encoding
                except UnicodeDecodeError:
                    continue
                    
            return "unknown"
            
        except Exception:
            return "unknown"

    def _count_lines(self, file_path: Path) -> int:
        """Contar líneas en archivo de texto"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def get_summary(self, metadata: Dict[str, Any]) -> str:
        """Generar resumen legible de metadatos"""
        try:
            if not metadata.get("success"):
                return f"Error: {metadata.get('error', 'Unknown error')}"
            
            basic = metadata.get("basic", {})
            specific = metadata.get("specific", {})
            
            summary = f"""📁 FILE METADATA SUMMARY:
            
🔸 File: {basic.get('filename', 'Unknown')}
🔸 Type: {basic.get('file_type', 'Unknown')} ({basic.get('extension', 'No ext')})
🔸 Size: {basic.get('size_mb', 0)} MB
🔸 Created: {basic.get('created_time', 'Unknown')[:19].replace('T', ' ')}
🔸 Modified: {basic.get('modified_time', 'Unknown')[:19].replace('T', ' ')}"""

            # Añadir detalles específicos según el tipo
            if specific.get("type") == "image":
                img_info = specific.get("image_info", {})
                summary += f"""
🖼️ Image Details:
🔸 Dimensions: {img_info.get('width', 'Unknown')} x {img_info.get('height', 'Unknown')}
🔸 Format: {img_info.get('format', 'Unknown')}
🔸 Color Mode: {img_info.get('mode', 'Unknown')}"""
                
                if specific.get("exif"):
                    summary += f"\n🔸 EXIF Data: {len(specific['exif'])} fields found"
                    
            elif specific.get("type") == "video":
                if specific.get("error"):
                    summary += f"\n🎬 Video: {specific['error']}"
                else:
                    video_info = specific.get("video_info", {})
                    format_info = specific.get("format", {})
                    summary += f"""
🎬 Video Details:
🔸 Resolution: {video_info.get('width', 'Unknown')} x {video_info.get('height', 'Unknown')}
🔸 Codec: {video_info.get('codec', 'Unknown')}
🔸 Duration: {format_info.get('duration', 'Unknown')}s
🔸 Frame Rate: {video_info.get('frame_rate', 'Unknown')}
🔸 Streams: {specific.get('streams_count', {}).get('total', 'Unknown')}"""
                    
                    if specific.get("creation_date"):
                        summary += f"\n🔸 Created: {specific['creation_date']}"
                        
            elif specific.get("type") == "audio":
                if specific.get("error"):
                    summary += f"\n🎵 Audio: {specific['error']}"
                else:
                    audio_info = specific.get("audio_info", {})
                    format_info = specific.get("format", {})
                    id3_tags = specific.get("id3_tags", {})
                    summary += f"""
🎵 Audio Details:
🔸 Codec: {audio_info.get('codec', 'Unknown')}
🔸 Duration: {format_info.get('duration', 'Unknown')}s
🔸 Sample Rate: {audio_info.get('sample_rate', 'Unknown')}Hz
🔸 Channels: {audio_info.get('channels', 'Unknown')}"""
                    
                    if id3_tags.get("title"):
                        summary += f"\n🔸 Title: {id3_tags['title']}"
                    if id3_tags.get("artist"):
                        summary += f"\n🔸 Artist: {id3_tags['artist']}"
            
            return summary
            
        except Exception as e:
            return f"Error generating summary: {e}"

# Instancia global
metadata_extractor = FileMetadataExtractor() 