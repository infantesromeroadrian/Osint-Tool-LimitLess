import streamlit as st
from controllers.dashboard_controller import DashboardController
from controllers.upload_controller import UploadController
from controllers.search_controller import SearchController
from controllers.transcription_controller import TranscriptionController
from controllers.image_analysis_controller import ImageAnalysisController
from load_env import load_environment

class LimitlessOSINT:
    """Main application class for Limitless OSINT tool."""
    
    def __init__(self):
        """Initialize the application with controllers."""
        self.dashboard_controller = DashboardController()
        self.upload_controller = UploadController()
        self.search_controller = SearchController()
        self.transcription_controller = TranscriptionController()
        self.image_analysis_controller = ImageAnalysisController()
        self.setup_config()
        
    def setup_config(self):
        """Configure the Streamlit app settings."""
        st.set_page_config(
            page_title="Limitless OSINT Tool",
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
    def run(self):
        """Run the Limitless OSINT application."""
        st.sidebar.title("🔍 Limitless OSINT")
        
        # Application tabs
        tabs = ["Dashboard", "Upload Documents", "Search Intelligence", "Audio Transcription", "Análisis de Imágenes"]
        selected_tab = st.sidebar.radio("Navigation", tabs)
        
        # Render selected tab
        if selected_tab == "Dashboard":
            self.dashboard_controller.render()
        elif selected_tab == "Upload Documents":
            self.upload_controller.render()
        elif selected_tab == "Search Intelligence":
            self.search_controller.render()
        elif selected_tab == "Audio Transcription":
            self.transcription_controller.render()
        elif selected_tab == "Análisis de Imágenes":
            self.image_analysis_controller.render()
            
        st.sidebar.markdown("---")
        st.sidebar.info("Limitless OSINT Tool - Powered by RAG Technology")

if __name__ == "__main__":
    # Load environment variables
    env_loaded = load_environment()
    
    if not env_loaded:
        st.error("OpenAI API key not found. Please set it in the .env file or as an environment variable.")
    
    # Start the app
    app = LimitlessOSINT()
    app.run() 