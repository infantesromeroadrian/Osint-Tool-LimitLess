"""
Metadata Utilities
Utilidades comunes para extracción de metadatos
"""

import os
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

def extract_basic_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extraer metadatos básicos del sistema de archivos
    Función común para todos los tipos de archivos
    """
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
            "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "accessed_time": datetime.fromtimestamp(stat.st_atime).isoformat(),
            "permissions": oct(stat.st_mode)[-3:]
        }
        
    except Exception as e:
        return {"error": str(e)}

def get_file_category(extension: str) -> str:
    """
    Determinar categoría del archivo por extensión
    Función centralizada para clasificación de archivos
    """
    categories = {
        'image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'},
        'document': {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.md', '.log'},
        'video': {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'},
        'audio': {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
    }
    
    extension_lower = extension.lower()
    for category, extensions in categories.items():
        if extension_lower in extensions:
            return category
    
    return "unknown"

def format_file_size(size_bytes: int) -> str:
    """
    Formatear tamaño de archivo en formato legible
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def format_duration(duration_seconds: float) -> str:
    """
    Formatear duración en formato legible (HH:MM:SS)
    """
    try:
        duration = float(duration_seconds)
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
            
    except (ValueError, TypeError):
        return "Unknown"

def generate_metadata_summary(metadata: Dict[str, Any]) -> str:
    """
    Generar resumen legible de metadatos
    Función centralizada para formateo de resúmenes
    """
    try:
        if not metadata.get("success"):
            return f"❌ Error: {metadata.get('error', 'Unknown error')}"
        
        basic = metadata.get("basic", {})
        specific = metadata.get("specific", {})
        
        # Encabezado básico
        summary = f"""📁 METADATA SUMMARY
        
🔸 File: {basic.get('filename', 'Unknown')}
🔸 Type: {get_file_category(basic.get('extension', ''))} ({basic.get('extension', 'No ext')})
🔸 Size: {format_file_size(basic.get('size_bytes', 0))}
🔸 Created: {format_timestamp(basic.get('created_time', ''))}
🔸 Modified: {format_timestamp(basic.get('modified_time', ''))}"""

        # Detalles específicos por tipo
        summary += _add_specific_details(specific)
        
        return summary
        
    except Exception as e:
        return f"❌ Error generating summary: {e}"

def _add_specific_details(specific: Dict[str, Any]) -> str:
    """
    Agregar detalles específicos al resumen según el tipo de archivo
    """
    details = ""
    file_type = specific.get("type", "unknown")
    
    if file_type == "image":
        details += _format_image_details(specific)
    elif file_type == "video":
        details += _format_video_details(specific)
    elif file_type == "audio":
        details += _format_audio_details(specific)
    elif file_type == "document":
        details += _format_document_details(specific)
    
    return details

def _format_image_details(specific: Dict[str, Any]) -> str:
    """Formatear detalles específicos de imagen"""
    if specific.get("error"):
        return f"\n🖼️ Image: {specific['error']}"
    
    img_info = specific.get("image_info", {})
    details = f"""
🖼️ Image Details:
🔸 Resolution: {img_info.get('width', 'Unknown')} x {img_info.get('height', 'Unknown')}
🔸 Format: {img_info.get('format', 'Unknown')}
🔸 Color Mode: {img_info.get('mode', 'Unknown')}"""
    
    if specific.get("exif"):
        details += f"\n🔸 EXIF Data: {len(specific['exif'])} fields"
    
    return details

def _format_video_details(specific: Dict[str, Any]) -> str:
    """Formatear detalles específicos de video"""
    if specific.get("error"):
        return f"\n🎬 Video: {specific['error']}"
    
    video_info = specific.get("video_info", {})
    format_info = specific.get("format", {})
    
    details = f"""
🎬 Video Details:
🔸 Resolution: {video_info.get('width', 'Unknown')} x {video_info.get('height', 'Unknown')}
🔸 Codec: {video_info.get('codec', 'Unknown')}
🔸 Duration: {format_duration(format_info.get('duration', 0))}
🔸 Frame Rate: {video_info.get('frame_rate', 'Unknown')}"""
    
    if specific.get("creation_date"):
        details += f"\n🔸 Created: {specific['creation_date']}"
    
    return details

def _format_audio_details(specific: Dict[str, Any]) -> str:
    """Formatear detalles específicos de audio"""
    if specific.get("error"):
        return f"\n🎵 Audio: {specific['error']}"
    
    audio_info = specific.get("audio_info", {})
    format_info = specific.get("format", {})
    id3_tags = specific.get("id3_tags", {})
    
    details = f"""
🎵 Audio Details:
🔸 Codec: {audio_info.get('codec', 'Unknown')}
🔸 Duration: {format_duration(format_info.get('duration', 0))}
🔸 Sample Rate: {audio_info.get('sample_rate', 'Unknown')}Hz
🔸 Channels: {audio_info.get('channels', 'Unknown')}"""
    
    if id3_tags.get("title"):
        details += f"\n🔸 Title: {id3_tags['title']}"
    if id3_tags.get("artist"):
        details += f"\n🔸 Artist: {id3_tags['artist']}"
    
    return details

def _format_document_details(specific: Dict[str, Any]) -> str:
    """Formatear detalles específicos de documento"""
    if specific.get("error"):
        return f"\n📄 Document: {specific['error']}"
    
    details = f"""
📄 Document Details:
🔸 Encoding: {specific.get('encoding', 'Unknown')}"""
    
    if specific.get("line_count"):
        details += f"\n🔸 Lines: {specific['line_count']}"
    if specific.get("word_count"):
        details += f"\n🔸 Words: {specific['word_count']}"
    
    return details

def format_timestamp(timestamp: str) -> str:
    """
    Formatear timestamp ISO para visualización
    """
    try:
        if timestamp:
            return timestamp[:19].replace('T', ' ')
        return "Unknown"
    except:
        return "Unknown" 