import os
import time
import openai
import tempfile
from pathlib import Path
import logging
from utils.case_path_resolver import CasePathResolver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TranscriptionService")

class TranscriptionService:
    """Service for transcribing audio files using OpenAI's Whisper model."""
    
    def __init__(self):
        """Initialize the transcription service with OpenAI API settings."""
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.case_resolver = CasePathResolver()
        
        # Get output directory based on active case
        self.output_dir = self.case_resolver.get_case_directory("transcriptions")
        
        # Initialize OpenAI client
        openai.api_key = self.api_key
    
    def transcribe_audio(self, audio_file, language=None):
        """
        Transcribe an audio file using OpenAI's Whisper model.
        
        Args:
            audio_file: The uploaded audio file object
            language: Optional language code to improve transcription accuracy
            
        Returns:
            tuple: (success, transcription_text or error_message)
        """
        if not self.api_key:
            return False, "OpenAI API key not found. Please set it in your environment."
        
        try:
            logger.info(f"Starting transcription for {audio_file.name}")
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio_file.name).suffix) as tmp_file:
                # Write uploaded audio to temp file
                tmp_file.write(audio_file.getvalue())
                temp_path = tmp_file.name
            
            # Build transcription options
            transcription_options = {
                "file": open(temp_path, "rb"),
                "model": "whisper-1",
            }
            
            if language:
                transcription_options["language"] = language
                
            # Call the OpenAI API
            start_time = time.time()
            response = openai.Audio.transcribe(**transcription_options)
            elapsed_time = time.time() - start_time
            
            # Clean up temp file
            os.unlink(temp_path)
            
            if response and hasattr(response, "text"):
                transcription_text = response.text
                logger.info(f"Transcription completed in {elapsed_time:.2f} seconds")
                
                # Make sure we're using the latest case directory
                self.output_dir = self.case_resolver.get_case_directory("transcriptions")
                
                # Save transcription to file
                output_filename = f"{Path(audio_file.name).stem}_transcription.txt"
                output_path = self.output_dir / output_filename
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(transcription_text)
                
                return True, transcription_text
            else:
                logger.error("Failed to get transcription text from API response")
                return False, "Failed to get transcription from API response"
                
        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            return False, f"Error during transcription: {str(e)}"
    
    def translate_text(self, text, target_language):
        """
        Translate text to the target language using OpenAI.
        
        Args:
            text: The text to translate
            target_language: The target language code or name
            
        Returns:
            tuple: (success, translated_text or error_message)
        """
        if not self.api_key:
            return False, "OpenAI API key not found. Please set it in your environment."
        
        try:
            logger.info(f"Starting translation to {target_language}")
            
            # Using OpenAI's GPT model to translate
            start_time = time.time()
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are a translator. Translate the following text to {target_language}. Provide only the translation, without explanations or notes."},
                    {"role": "user", "content": text}
                ],
                temperature=0.3
            )
            
            elapsed_time = time.time() - start_time
            
            if response and "choices" in response and len(response["choices"]) > 0:
                translated_text = response["choices"][0]["message"]["content"].strip()
                logger.info(f"Translation completed in {elapsed_time:.2f} seconds")
                
                # Make sure we're using the latest case directory
                self.output_dir = self.case_resolver.get_case_directory("transcriptions")
                
                # Save translation to file
                timestamp = int(time.time())
                output_filename = f"translation_{target_language}_{timestamp}.txt"
                output_path = self.output_dir / output_filename
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(translated_text)
                
                return True, translated_text
            else:
                logger.error("Failed to get translation from API response")
                return False, "Failed to get translation from API response"
                
        except Exception as e:
            logger.error(f"Error during translation: {str(e)}")
            return False, f"Error during translation: {str(e)}"
    
    def get_saved_transcriptions(self):
        """
        Get a list of all saved transcription files.
        
        Returns:
            list: List of transcription file paths
        """
        # Make sure we're using the latest case directory
        self.output_dir = self.case_resolver.get_case_directory("transcriptions")
        
        transcription_files = list(self.output_dir.glob("*_transcription.txt"))
        return [str(f) for f in transcription_files]
    
    def read_transcription(self, filename):
        """
        Read a transcription file.
        
        Args:
            filename: The name of the transcription file
            
        Returns:
            str: The transcription text or error message
        """
        # Make sure we're using the latest case directory
        self.output_dir = self.case_resolver.get_case_directory("transcriptions")
        
        file_path = self.output_dir / filename
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading transcription file: {str(e)}")
            return f"Error reading file: {str(e)}" 