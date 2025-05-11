import streamlit as st
from controllers.controllers import BaseController
from services.document_service import DocumentService

class UploadController(BaseController):
    """Controller for document upload and processing."""
    
    def __init__(self):
        """Initialize upload controller with required services."""
        self.document_service = DocumentService()
    
    def render(self):
        """Render the upload and document processing view."""
        st.title("📤 Upload Intelligence Documents")
        
        # Get document counts and stats
        doc_stats = self.document_service.get_document_stats()
        
        # Display instructions and current stats
        st.markdown("""
        ### Upload documents to extract and analyze intelligence data
        
        Documents uploaded here will be processed and indexed for searching with the RAG system.
        You must upload documents before using the Search Intelligence features.
        """)
        
        # Display current document stats
        st.info(f"Currently indexed: {doc_stats['total_documents']} documents with {doc_stats['total_chunks']} text chunks.")
        
        # File upload section
        uploaded_files = st.file_uploader(
            "Upload documents (.pdf, .csv, .txt, etc.)", 
            type=["pdf", "csv", "txt", "docx", "xlsx", "json", "html"],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            with st.form(key="processing_options"):
                st.subheader("Processing Options")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    chunk_size = st.slider("Chunk Size", 100, 1000, 500, 50,
                                          help="Number of characters in each document chunk. Smaller chunks give more precise results but may lose context.")
                    chunk_overlap = st.slider("Chunk Overlap", 0, 200, 50, 10,
                                             help="Number of characters that overlap between chunks. Higher overlap prevents context loss at chunk boundaries.")
                
                with col2:
                    embedding_model = st.selectbox(
                        "Embedding Model",
                        options=["all-MiniLM-L6-v2", "text-embedding-ada-002"],
                        index=0,
                        help="Model used to create document embeddings. 'all-MiniLM-L6-v2' is faster, 'text-embedding-ada-002' is more accurate but uses OpenAI API."
                    )
                    
                    preprocessing_options = st.multiselect(
                        "Preprocessing Steps",
                        options=["Remove stopwords", "Lemmatization", "Named Entity Recognition"],
                        default=["Remove stopwords"],
                        help="Text preprocessing steps to optimize document indexing."
                    )
                
                process_button = st.form_submit_button("Process Documents")
                
                if process_button:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Process each file
                    for i, file in enumerate(uploaded_files):
                        progress = (i + 1) / len(uploaded_files)
                        status_text.text(f"Processing {file.name}...")
                        
                        # Process the document
                        result = self.document_service.process_document(
                            file,
                            chunk_size=chunk_size,
                            chunk_overlap=chunk_overlap,
                            embedding_model=embedding_model,
                            preprocessing_options=preprocessing_options
                        )
                        
                        progress_bar.progress(progress)
                    
                    status_text.text("All documents processed successfully!")
                    st.success(f"Processed {len(uploaded_files)} documents and indexed for intelligence analysis.")
                    
                    # Update stats after processing
                    new_stats = self.document_service.get_document_stats()
                    st.info(f"Now indexed: {new_stats['total_documents']} documents with {new_stats['total_chunks']} text chunks.")
                    
                    # Prompt user to try searching
                    st.markdown("### Next Steps")
                    st.markdown("Your documents are now indexed! Go to the **Search Intelligence** tab to query your data.")
        else:
            st.warning("""
            No files uploaded yet. Upload one or more documents to begin processing and analysis.
            
            After uploading and processing documents, you can use the Search Intelligence features to query the information.
            """) 