"""
Media Metadata Processor
Procesador especializado para videos y audios usando FFmpeg
"""

import subprocess
import json
from typing import Dict, Any, List
from pathlib import Path
from ..base_processor import BaseMetadataProcessor

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

class MediaMetadataProcessor(BaseMetadataProcessor):
    """
    Procesador especializado para metadatos de video y audio
    Utiliza FFprobe para extraer información detallada
    """
    
    VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
    AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
    
    def __init__(self):
        super().__init__("media")
    
    def can_process(self, file_path: Path) -> bool:
        """Verificar si puede procesar el archivo multimedia"""
        extension = file_path.suffix.lower()
        return extension in self.VIDEO_EXTENSIONS or extension in self.AUDIO_EXTENSIONS
    
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extraer metadatos de archivo multimedia"""
        if not FFMPEG_AVAILABLE:
            return self.get_error_response(
                "FFmpeg not available", 
                "Install FFmpeg to extract media metadata"
            )
        
        try:
            # Ejecutar ffprobe
            raw_metadata = self._run_ffprobe(file_path)
            
            # Determinar tipo de archivo
            file_type = self._determine_file_type(file_path)
            
            # Procesar según el tipo
            if file_type == "video":
                return self._process_video_metadata(raw_metadata, file_path)
            else:
                return self._process_audio_metadata(raw_metadata, file_path)
                
        except Exception as e:
            error_msg = str(e)
            self.log_error(file_path, error_msg)
            return self.get_error_response(error_msg)
    
    def _run_ffprobe(self, file_path: Path) -> Dict[str, Any]:
        """Ejecutar ffprobe y obtener metadatos raw"""
        cmd = [
            "ffprobe", "-v", "error", "-print_format", "json",
            "-show_format", "-show_streams", str(file_path)
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            raise Exception(f"FFprobe error: {result.stderr}")
        
        return json.loads(result.stdout)
    
    def _determine_file_type(self, file_path: Path) -> str:
        """Determinar si es video o audio"""
        extension = file_path.suffix.lower()
        return "video" if extension in self.VIDEO_EXTENSIONS else "audio"
    
    def _process_video_metadata(self, metadata: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """Procesar metadatos de video"""
        format_info = metadata.get("format", {})
        streams = metadata.get("streams", [])
        
        # Separar streams
        video_streams = [s for s in streams if s.get("codec_type") == "video"]
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
        
        # Información principal de video
        video_info = self._extract_video_stream_info(video_streams)
        
        # Información de audio
        audio_info = self._extract_audio_stream_info(audio_streams)
        
        # Información del formato
        format_metadata = self._extract_format_info(format_info)
        
        # Tags y fechas
        tags = format_info.get("tags", {})
        creation_date = self._extract_creation_date(tags)
        
        result = {
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
            }
        }
        
        self.log_success(file_path, len(tags))
        return result
    
    def _process_audio_metadata(self, metadata: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """Procesar metadatos de audio"""
        format_info = metadata.get("format", {})
        streams = metadata.get("streams", [])
        
        # Información principal de audio
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
        audio_info = self._extract_audio_stream_info(audio_streams)
        
        # Información del formato
        format_metadata = self._extract_format_info(format_info)
        
        # Tags (ID3, etc.)
        tags = format_info.get("tags", {})
        id3_info = self._extract_id3_tags(tags)
        
        result = {
            "type": "audio",
            "format": format_metadata,
            "audio_info": audio_info,
            "id3_tags": id3_info,
            "all_tags": tags,
            "streams_count": len(audio_streams)
        }
        
        self.log_success(file_path, len(tags))
        return result
    
    def _extract_video_stream_info(self, video_streams: List[Dict]) -> Dict[str, Any]:
        """Extraer información del stream de video principal"""
        if not video_streams:
            return {}
        
        stream = video_streams[0]  # Stream principal
        return {
            "codec": stream.get("codec_name"),
            "width": stream.get("width"),
            "height": stream.get("height"),
            "aspect_ratio": stream.get("display_aspect_ratio"),
            "frame_rate": stream.get("r_frame_rate"),
            "bit_rate": stream.get("bit_rate"),
            "pixel_format": stream.get("pix_fmt"),
            "duration": stream.get("duration")
        }
    
    def _extract_audio_stream_info(self, audio_streams: List[Dict]) -> Dict[str, Any]:
        """Extraer información del stream de audio principal"""
        if not audio_streams:
            return {}
        
        stream = audio_streams[0]  # Stream principal
        return {
            "codec": stream.get("codec_name"),
            "sample_rate": stream.get("sample_rate"),
            "channels": stream.get("channels"),
            "channel_layout": stream.get("channel_layout"),
            "bit_rate": stream.get("bit_rate"),
            "duration": stream.get("duration"),
            "bits_per_sample": stream.get("bits_per_raw_sample")
        }
    
    def _extract_format_info(self, format_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer información del formato/contenedor"""
        return {
            "format_name": format_info.get("format_name"),
            "format_long_name": format_info.get("format_long_name"),
            "duration": format_info.get("duration"),
            "size": format_info.get("size"),
            "bit_rate": format_info.get("bit_rate"),
            "nb_streams": format_info.get("nb_streams"),
            "nb_programs": format_info.get("nb_programs")
        }
    
    def _extract_creation_date(self, tags: Dict[str, Any]) -> str:
        """Extraer fecha de creación de los tags"""
        return tags.get("creation_time") or tags.get("date") or None
    
    def _extract_id3_tags(self, tags: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer tags ID3 comunes"""
        return {
            "title": tags.get("title") or tags.get("TIT2"),
            "artist": tags.get("artist") or tags.get("TPE1"),
            "album": tags.get("album") or tags.get("TALB"),
            "date": tags.get("date") or tags.get("TYER"),
            "genre": tags.get("genre") or tags.get("TCON"),
            "track": tags.get("track") or tags.get("TRCK")
        } 