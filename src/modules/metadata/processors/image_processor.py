"""
Image Metadata Processor
Procesador especializado para metadatos de imágenes
"""

from typing import Dict, Any
from pathlib import Path
from ..base_processor import BaseMetadataProcessor

# Importación condicional de PIL
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class ImageMetadataProcessor(BaseMetadataProcessor):
    """
    Procesador especializado para metadatos de imágenes
    Maneja EXIF, dimensiones, colores dominantes, etc.
    """
    
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    
    def __init__(self):
        super().__init__("image")
    
    def can_process(self, file_path: Path) -> bool:
        """Verificar si puede procesar el archivo de imagen"""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS
    
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extraer metadatos completos de imagen"""
        if not PIL_AVAILABLE:
            return self.get_error_response("PIL not available for image metadata")
        
        try:
            with Image.open(file_path) as img:
                # Información básica
                basic_info = self._extract_basic_info(img)
                
                # Metadatos EXIF
                exif_data = self._extract_exif_data(img)
                
                # Análisis de colores
                color_palette = self._extract_color_palette(img)
                
                result = {
                    "type": "image",
                    "image_info": basic_info,
                    "exif": exif_data,
                    "color_palette": color_palette
                }
                
                self.log_success(file_path, len(exif_data))
                return result
                
        except Exception as e:
            error_msg = str(e)
            self.log_error(file_path, error_msg)
            return self.get_error_response(error_msg)
    
    def _extract_basic_info(self, img: Image.Image) -> Dict[str, Any]:
        """Extraer información básica de la imagen"""
        return {
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "mode": img.mode,
            "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info,
            "resolution": (img.width, img.height),
            "aspect_ratio": round(img.width / img.height, 2) if img.height > 0 else 0
        }
    
    def _extract_exif_data(self, img: Image.Image) -> Dict[str, str]:
        """Extraer datos EXIF de la imagen"""
        exif_data = {}
        try:
            exif = img.getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, f"Unknown_{tag_id}")
                    exif_data[tag] = str(value)
        except AttributeError:
            # Fallback para versiones antiguas de PIL
            pass
        return exif_data
    
    def _extract_color_palette(self, img: Image.Image, num_colors: int = 5) -> list:
        """Extraer colores dominantes de la imagen"""
        try:
            # Redimensionar para análisis rápido
            img_small = img.resize((50, 50))
            colors = img_small.getcolors(maxcolors=256)
            
            if not colors:
                return []
            
            # Ordenar por frecuencia
            sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)
            dominant = []
            
            for count, color in sorted_colors[:num_colors]:
                if isinstance(color, tuple) and len(color) >= 3:
                    hex_color = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                    dominant.append({
                        "color": hex_color,
                        "frequency": count,
                        "percentage": round((count / sum(c[0] for c in colors)) * 100, 1)
                    })
            
            return dominant
            
        except Exception as e:
            self.logger.warning(f"Color analysis failed: {e}")
            return [] 