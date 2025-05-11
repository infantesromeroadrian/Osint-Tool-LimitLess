import os
import tempfile
from typing import Dict, List, BinaryIO, Any
from services.services import BaseService
from models.document_model import DocumentModel
from utils.document_processor import DocumentProcessor
from utils.embedding_generator import EmbeddingGenerator
from utils.vector_store import VectorStore

class DocumentService(BaseService):
    """Service for document processing and vectorization."""
    
    def __init__(self):
        """Initialize document service with required dependencies."""
        self.document_model = DocumentModel()
        self.document_processor = DocumentProcessor()
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore()
    
    def process_document(
        self, 
        file: BinaryIO, 
        chunk_size: int = 500, 
        chunk_overlap: int = 50,
        embedding_model: str = "all-MiniLM-L6-v2",
        preprocessing_options: List[str] = None
    ) -> Dict[str, Any]:
        """Process a document and store it in the vector database.
        
        Args:
            file: The uploaded file object
            chunk_size: Size of text chunks for processing
            chunk_overlap: Overlap between chunks
            embedding_model: Model to use for embeddings
            preprocessing_options: NLP preprocessing steps to apply
            
        Returns:
            Dictionary with processing results
        """
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.name.split('.')[-1]}") as temp_file:
            temp_file.write(file.getbuffer())
            temp_path = temp_file.name
            print(f"DEBUG: Saved temporary file to {temp_path}")
        
        try:
            # Extract text from document
            print(f"DEBUG: Attempting to extract text from {file.name}")
            text = self.document_processor.extract_text(temp_path)
            print(f"DEBUG: Extracted {len(text)} characters of text")
            if len(text) < 100:
                print(f"DEBUG: Text sample: '{text[:100]}'")
            else:
                print(f"DEBUG: Text sample: '{text[:100]}...'")
            
            if not text.strip():
                print("DEBUG: WARNING - Extracted text is empty or whitespace only!")
                return {
                    "error": "No text could be extracted from the document",
                    "success": False
                }
            
            # Preprocess text
            print(f"DEBUG: Preprocessing text with options: {preprocessing_options or ['Remove stopwords']}")
            preprocessed_text = self.document_processor.preprocess_text(
                text, 
                options=preprocessing_options or ["Remove stopwords"]
            )
            print(f"DEBUG: After preprocessing, text length is {len(preprocessed_text)} characters")
            
            # Split text into chunks
            print(f"DEBUG: Splitting text into chunks (size={chunk_size}, overlap={chunk_overlap})")
            chunks = self.document_processor.split_text(
                preprocessed_text,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            print(f"DEBUG: Created {len(chunks)} chunks")
            
            if len(chunks) == 0:
                print("DEBUG: WARNING - No chunks were created from the text!")
                return {
                    "error": "Document was processed but no chunks were created",
                    "success": False
                }
                
            # Print first chunk as sample
            if chunks:
                print(f"DEBUG: First chunk sample: '{chunks[0][:100]}...'")
            
            # Generate embeddings
            print(f"DEBUG: Generating embeddings with model {embedding_model}")
            embeddings = self.embedding_generator.generate_embeddings(
                chunks,
                model_name=embedding_model
            )
            print(f"DEBUG: Generated {len(embeddings)} embeddings")
            
            # Store in vector database
            print(f"DEBUG: Storing document in vector database")
            document_id = self.vector_store.add_document(
                document_name=file.name,
                chunks=chunks,
                embeddings=embeddings,
                metadata={
                    "filename": file.name,
                    "file_type": file.name.split(".")[-1].lower(),
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "embedding_model": embedding_model,
                    "preprocessing": preprocessing_options or ["Remove stopwords"]
                }
            )
            print(f"DEBUG: Document stored with ID {document_id}")
            
            # Save document metadata
            print(f"DEBUG: Saving document metadata")
            self.document_model.add_document(
                document_id=document_id,
                name=file.name,
                file_type=file.name.split(".")[-1].lower(),
                chunk_count=len(chunks),
                processing_options={
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "embedding_model": embedding_model,
                    "preprocessing": preprocessing_options or ["Remove stopwords"]
                }
            )
            print(f"DEBUG: Document metadata saved")
            
            # Check document stats after adding
            stats = self.vector_store.get_collection_stats()
            print(f"DEBUG: Vector store stats after adding document: {stats}")
            
            return {
                "document_id": document_id,
                "name": file.name,
                "chunk_count": len(chunks),
                "success": True
            }
            
        except Exception as e:
            # More detailed error logging
            import traceback
            print(f"DEBUG: ERROR processing document {file.name}: {str(e)}")
            print(f"DEBUG: Error traceback: {traceback.format_exc()}")
            return {
                "error": str(e),
                "success": False
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"DEBUG: Removed temporary file {temp_path}")
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about the indexed documents.
        
        Returns:
            Dictionary with document statistics
        """
        try:
            # Get document list from the model
            documents = self.document_model.get_all_documents()
            print(f"DEBUG: Found {len(documents)} documents in document model")
            
            # Get vector store stats
            vector_stats = self.vector_store.get_collection_stats()
            print(f"DEBUG: Vector store stats: {vector_stats}")
            
            # Calculate statistics
            total_documents = len(documents)
            total_chunks = vector_stats.get("total_chunks", 0)
            
            # Get document types
            file_types = {}
            for doc in documents:
                file_type = doc.get("file_type", "unknown")
                if file_type in file_types:
                    file_types[file_type] += 1
                else:
                    file_types[file_type] = 1
            
            return {
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "file_types": file_types,
                "vector_collection": vector_stats.get("collection_name", "documents")
            }
            
        except Exception as e:
            # Handle any errors gracefully
            import traceback
            print(f"DEBUG: ERROR getting document stats: {str(e)}")
            print(f"DEBUG: Error traceback: {traceback.format_exc()}")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "file_types": {},
                "error": str(e)
            } 