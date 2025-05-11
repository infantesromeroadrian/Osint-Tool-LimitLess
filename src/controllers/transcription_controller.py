import streamlit as st
import os
import time
from pathlib import Path
from services.transcription_service import TranscriptionService

class TranscriptionController:
    """Controller for audio transcription interface."""
    
    def __init__(self):
        """Initialize the transcription controller."""
        self.transcription_service = TranscriptionService()
        self.supported_formats = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
        self.available_languages = {
            "Spanish": "Spanish",
            "English": "English",
            "French": "French",
            "German": "German",
            "Italian": "Italian",
            "Portuguese": "Portuguese",
            "Dutch": "Dutch",
            "Russian": "Russian",
            "Chinese": "Chinese",
            "Japanese": "Japanese",
            "Korean": "Korean",
            "Arabic": "Arabic",
            "Hindi": "Hindi",
            "Turkish": "Turkish"
        }

    def render(self):
        """Render the transcription interface."""
        st.title("🎙️ Audio Transcription")
        st.write("Upload audio files and transcribe them using OpenAI's Whisper model.")
        
        # Create tabs for upload and history
        tab1, tab2 = st.tabs(["Transcribe Audio", "Transcription History"])
        
        with tab1:
            self._render_upload_section()
            
        with tab2:
            self._render_history_section()
            
    def _render_upload_section(self):
        """Render the audio upload and transcription section."""
        st.header("Upload Audio File")
        
        # Language selection
        language_options = [
            "None (Auto-detect)", "en", "es", "fr", "de", "it", "pt", "nl", 
            "ru", "zh", "ja", "ko", "ar", "hi", "tr"
        ]
        language = st.selectbox(
            "Select language (optional, improves accuracy)",
            language_options,
            key="language_selector"
        )
        
        if language == "None (Auto-detect)":
            language = None
            
        # File uploader
        audio_file = st.file_uploader(
            "Upload an audio file",
            type=self.supported_formats,
            help=f"Supported formats: {', '.join(self.supported_formats)}",
            key="audio_uploader"
        )
        
        if audio_file is not None:
            st.audio(audio_file, format="audio/mp3")
            
            st.info(f"File uploaded: {audio_file.name} ({round(audio_file.size / 1024 / 1024, 2)} MB)")
            
            if st.button("🎯 Transcribe Audio", key="transcribe_button"):
                with st.spinner("Transcribing audio... This may take a while depending on the file size."):
                    success, result = self.transcription_service.transcribe_audio(audio_file, language)
                    
                    if success:
                        st.session_state.transcription = result
                        st.success("Transcription completed successfully!")
                        st.text_area(
                            "Transcription", 
                            result, 
                            height=300,
                            key="upload_transcription_result"
                        )
                        
                        # Offer download option
                        st.download_button(
                            label="Download Transcription",
                            data=result,
                            file_name=f"{Path(audio_file.name).stem}_transcription.txt",
                            mime="text/plain",
                            key="upload_download_button"
                        )
                        
                        # Translation section
                        self._render_translation_section(result, section="upload")
                    else:
                        st.error(f"Transcription failed: {result}")
            
            # Check if we have a transcription from a previous run
            elif hasattr(st.session_state, 'transcription') and st.session_state.transcription:
                st.text_area(
                    "Previous Transcription", 
                    st.session_state.transcription, 
                    height=300,
                    key="previous_transcription_result"
                )
                
                # Translation section for previous transcription
                self._render_translation_section(st.session_state.transcription, section="previous")
            
    def _render_translation_section(self, text_to_translate, section="default"):
        """
        Render the translation section.
        
        Args:
            text_to_translate: The text to translate
            section: Section identifier to create unique widget keys ("upload", "history", "previous")
        """
        st.subheader("🌐 Translate Transcription")
        st.write("Translate the transcription to a different language.")
        
        # Target language selection
        target_language = st.selectbox(
            "Select target language",
            list(self.available_languages.keys()),
            key=f"translation_language_selector_{section}"
        )
        
        if st.button("🔄 Translate", key=f"translate_button_{section}"):
            with st.spinner(f"Translating to {target_language}... This may take a moment."):
                success, translated_text = self.transcription_service.translate_text(
                    text_to_translate, 
                    self.available_languages[target_language]
                )
                
                if success:
                    st.success(f"Translation to {target_language} completed successfully!")
                    st.text_area(
                        f"Translated Text ({target_language})", 
                        translated_text, 
                        height=300,
                        key=f"translation_result_{section}"
                    )
                    
                    # Offer download option
                    st.download_button(
                        label=f"Download {target_language} Translation",
                        data=translated_text,
                        file_name=f"translation_{target_language.lower()}_{int(1000*time.time())}.txt",
                        mime="text/plain",
                        key=f"translation_download_button_{section}"
                    )
                else:
                    st.error(f"Translation failed: {translated_text}")
            
    def _render_history_section(self):
        """Render the transcription history section."""
        st.header("Previous Transcriptions")
        
        transcription_files = self.transcription_service.get_saved_transcriptions()
        
        if not transcription_files:
            st.info("No transcriptions found. Transcribe an audio file to see it here.")
            return
            
        # Display list of transcription files
        file_names = [Path(f).name for f in transcription_files]
        selected_file = st.selectbox(
            "Select a transcription to view", 
            file_names,
            key="history_file_selector"
        )
        
        if selected_file:
            transcription_text = self.transcription_service.read_transcription(selected_file)
            st.text_area(
                "Transcription", 
                transcription_text, 
                height=300,
                key="history_transcription_result"
            )
            
            # Offer download option
            st.download_button(
                label="Download Transcription",
                data=transcription_text,
                file_name=selected_file,
                mime="text/plain",
                key="history_download_button"
            )
            
            # Translation section for history
            self._render_translation_section(transcription_text, section="history") 