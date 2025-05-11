import streamlit as st
import os
import time
from pathlib import Path
from services.image_analysis_service import ImageAnalysisService

class ImageAnalysisController:
    """Controller for image analysis interface."""
    
    def __init__(self):
        """Initialize the image analysis controller."""
        self.image_analysis_service = ImageAnalysisService()
        self.supported_formats = ["jpg", "jpeg", "png", "webp", "bmp"]

    def render(self):
        """Render the image analysis interface."""
        st.title("🖼️ Análisis de Imágenes")
        st.write("Sube imágenes para analizarlas usando GPT-4.1 con capacidades de visión.")
        
        # Create tabs for upload and history
        tab1, tab2 = st.tabs(["Analizar Imagen", "Historial de Análisis"])
        
        with tab1:
            self._render_upload_section()
            
        with tab2:
            self._render_history_section()
            
    def _render_upload_section(self):
        """Render the image upload and analysis section."""
        st.header("Subir Imagen")
        
        # Custom prompt option
        use_custom_prompt = st.checkbox("Usar instrucción personalizada", key="use_custom_prompt")
        
        prompt = None
        if use_custom_prompt:
            prompt = st.text_area(
                "Escribe instrucciones específicas para el análisis:",
                "Analiza esta imagen en detalle. Describe lo que ves, incluye objetos, personas, textos, colores, y cualquier elemento relevante.",
                height=100,
                key="prompt_input"
            )
                    
        # File uploader
        image_file = st.file_uploader(
            "Sube una imagen",
            type=self.supported_formats,
            help=f"Formatos soportados: {', '.join(self.supported_formats)}",
            key="image_uploader"
        )
        
        if image_file is not None:
            # Display uploaded image
            st.image(image_file, caption="Imagen subida", use_column_width=True)
            
            st.info(f"Archivo subido: {image_file.name} ({round(image_file.size / 1024 / 1024, 2)} MB)")
            
            if st.button("🔍 Analizar Imagen", key="analyze_button"):
                with st.spinner("Analizando imagen... Esto puede tomar un momento."):
                    success, result = self.image_analysis_service.analyze_image(image_file, prompt)
                    
                    if success:
                        st.session_state.analysis_result = result
                        st.success("Análisis completado con éxito!")
                        
                        # Display analysis
                        st.subheader("Resultado del Análisis")
                        st.markdown(result)
                        
                        # Use current timestamp instead of file modification time
                        timestamp = int(time.time())
                        
                        # Offer download option
                        st.download_button(
                            label="Descargar Análisis",
                            data=result,
                            file_name=f"{Path(image_file.name).stem}_analysis_{timestamp}.txt",
                            mime="text/plain",
                            key="download_analysis_button"
                        )
                    else:
                        st.error(f"Error en el análisis: {result}")
            
            # Check if we have an analysis from a previous run
            elif hasattr(st.session_state, 'analysis_result') and st.session_state.analysis_result:
                st.subheader("Resultado del Análisis Previo")
                st.markdown(st.session_state.analysis_result)
                
                # Use current timestamp instead of file modification time
                timestamp = int(time.time())
                
                # Offer download option
                st.download_button(
                    label="Descargar Análisis",
                    data=st.session_state.analysis_result,
                    file_name=f"previous_analysis_{timestamp}.txt",
                    mime="text/plain",
                    key="download_previous_analysis_button"
                )
            
    def _render_history_section(self):
        """Render the analysis history section."""
        st.header("Análisis Anteriores")
        
        analysis_files = self.image_analysis_service.get_saved_analyses()
        
        if not analysis_files:
            st.info("No se encontraron análisis previos. Analiza una imagen para verla aquí.")
            return
            
        # Display list of analysis files
        file_names = [Path(f).name for f in analysis_files]
        selected_file = st.selectbox(
            "Selecciona un análisis para ver", 
            file_names,
            key="history_file_selector"
        )
        
        if selected_file:
            analysis_text = self.image_analysis_service.read_analysis(selected_file)
            
            # Display analysis
            st.subheader("Resultado del Análisis")
            st.markdown(analysis_text)
            
            # Offer download option
            st.download_button(
                label="Descargar Análisis",
                data=analysis_text,
                file_name=selected_file,
                mime="text/plain",
                key="history_download_button"
            ) 