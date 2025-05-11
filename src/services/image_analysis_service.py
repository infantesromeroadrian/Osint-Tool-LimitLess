import os
import time
import base64
import openai
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ImageAnalysisService")

class ImageAnalysisService:
    """Service for analyzing images using OpenAI's Vision API."""
    
    def __init__(self):
        """Initialize the image analysis service with OpenAI API settings."""
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.output_dir = Path(os.path.abspath("data/image_analysis"))
        
        # Ensure the output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize OpenAI client
        openai.api_key = self.api_key
    
    def encode_image(self, image_file):
        """
        Encode image file to base64 string for API request.
        
        Args:
            image_file: The uploaded image file object
            
        Returns:
            str: Base64 encoded image
        """
        return base64.b64encode(image_file.getvalue()).decode('utf-8')
    
    def analyze_image(self, image_file, prompt=None):
        """
        Analyze an image using OpenAI's Vision API.
        
        Args:
            image_file: The uploaded image file object
            prompt: Custom prompt for image analysis (optional)
            
        Returns:
            tuple: (success, analysis_text or error_message)
        """
        if not self.api_key:
            return False, "OpenAI API key not found. Please set it in your environment."
        
        try:
            logger.info(f"Starting image analysis for {image_file.name}")
            
            # Encode image
            base64_image = self.encode_image(image_file)
            
            # Default prompt if none provided
            if not prompt:
                prompt = "Analiza esta imagen en detalle. Describe lo que ves, incluye objetos, personas, textos, colores, y cualquier elemento relevante. Si hay texto visible, transcríbelo. Si la imagen muestra algún dato sensible, menciónalo."
            
            # Prepare API request
            start_time = time.time()
            
            # Call the OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-4o",  # Using GPT-4 with vision capabilities
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente experto en analizar imágenes con alta precisión. Describe detalladamente el contenido visual y proporciona insights profundos sobre lo que observas."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            elapsed_time = time.time() - start_time
            
            # Process response
            if response and "choices" in response and len(response["choices"]) > 0:
                analysis_text = response["choices"][0]["message"]["content"]
                logger.info(f"Image analysis completed in {elapsed_time:.2f} seconds")
                
                # Save analysis to file
                timestamp = int(time.time())
                output_filename = f"{Path(image_file.name).stem}_analysis_{timestamp}.txt"
                output_path = self.output_dir / output_filename
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(analysis_text)
                
                return True, analysis_text
            else:
                logger.error("Failed to get analysis from API response")
                return False, "Failed to get analysis from API response"
                
        except Exception as e:
            logger.error(f"Error during image analysis: {str(e)}")
            return False, f"Error during image analysis: {str(e)}"
    
    def get_saved_analyses(self):
        """
        Get a list of all saved image analysis files.
        
        Returns:
            list: List of analysis file paths
        """
        analysis_files = list(self.output_dir.glob("*_analysis_*.txt"))
        return sorted([str(f) for f in analysis_files], reverse=True)
    
    def read_analysis(self, filename):
        """
        Read an analysis file.
        
        Args:
            filename: The name of the analysis file
            
        Returns:
            str: The analysis text or error message
        """
        file_path = self.output_dir / filename
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading analysis file: {str(e)}")
            return f"Error reading file: {str(e)}" 