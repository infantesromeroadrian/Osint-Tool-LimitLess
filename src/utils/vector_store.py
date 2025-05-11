import os
import numpy as np
from typing import List, Dict, Any, Union
import chromadb
from chromadb.config import Settings
from utils.helpers import generate_unique_id, ensure_directory_exists
from utils.case_path_resolver import CasePathResolver

class VectorStore:
    """Vector database for storing and retrieving document embeddings."""
    
    def __init__(self, persist_directory: str = None):
        """Initialize the vector store.
        
        Args:
            persist_directory: Directory to persist the database (will use case directory if None)
        """
        # Get path based on active case if not specified
        if persist_directory is None:
            case_resolver = CasePathResolver()
            persist_directory = str(case_resolver.get_case_directory("chroma_db"))
        
        # Ensure the persistence directory exists
        ensure_directory_exists(persist_directory)
        print(f"DEBUG: Vector store using persistence directory: {persist_directory}")
        
        # Initialize ChromaDB client
        try:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            print(f"DEBUG: ChromaDB client initialized successfully")
        except Exception as e:
            print(f"DEBUG: ERROR initializing ChromaDB client: {str(e)}")
            raise
        
        # Create or get the collection
        try:
            self.collection = self.client.get_or_create_collection("documents")
            print(f"DEBUG: ChromaDB collection 'documents' initialized")
            
            # Get initial collection stats
            count = self.collection.count()
            print(f"DEBUG: Initial collection contains {count} documents")
        except Exception as e:
            print(f"DEBUG: ERROR accessing ChromaDB collection: {str(e)}")
            raise
    
    def add_document(
        self, 
        document_name: str, 
        chunks: List[str], 
        embeddings: List[np.ndarray],
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add a document's chunks and embeddings to the vector store.
        
        Args:
            document_name: Name of the document
            chunks: List of text chunks
            embeddings: List of embedding vectors
            metadata: Document metadata
            
        Returns:
            Unique document ID
        """
        document_id = generate_unique_id()
        print(f"DEBUG: Adding document {document_name} with ID {document_id}")
        print(f"DEBUG: Document has {len(chunks)} chunks and {len(embeddings)} embeddings")
        
        if len(chunks) == 0:
            print("DEBUG: ERROR - No chunks provided to add_document()")
            raise ValueError("No chunks provided to add_document()")
            
        if len(embeddings) == 0:
            print("DEBUG: ERROR - No embeddings provided to add_document()")
            raise ValueError("No embeddings provided to add_document()")
            
        if len(chunks) != len(embeddings):
            print(f"DEBUG: ERROR - Chunk count ({len(chunks)}) and embedding count ({len(embeddings)}) don't match")
            raise ValueError(f"Chunk count ({len(chunks)}) and embedding count ({len(embeddings)}) must match")
        
        # Prepare metadata for each chunk
        metadatas = []
        for i in range(len(chunks)):
            chunk_metadata = {
                "document_id": document_id,
                "document_name": document_name,
                "chunk_index": i
            }
            
            # Add document metadata if provided
            if metadata:
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        chunk_metadata[key] = value
            
            metadatas.append(chunk_metadata)
        
        # Generate unique IDs for each chunk
        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        
        # Convert numpy arrays to lists for ChromaDB
        embeddings_list = [embedding.tolist() for embedding in embeddings]
        
        # Add to collection
        try:
            print(f"DEBUG: Adding chunks to ChromaDB collection")
            self.collection.add(
                embeddings=embeddings_list,
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            print(f"DEBUG: Successfully added {len(chunks)} chunks to ChromaDB")
            
            # Verify the chunks were added
            count_after = self.collection.count()
            print(f"DEBUG: Collection now contains {count_after} total chunks")
            
            # Try to retrieve one of the added chunks to confirm
            chunk_id = ids[0]
            try:
                result = self.collection.get(ids=[chunk_id])
                if result and len(result["documents"]) > 0:
                    print(f"DEBUG: Successfully verified chunk retrieval")
                else:
                    print(f"DEBUG: WARNING - Could not retrieve newly added chunk with ID {chunk_id}")
            except Exception as e:
                print(f"DEBUG: ERROR verifying chunk retrieval: {str(e)}")
            
        except Exception as e:
            print(f"DEBUG: ERROR adding chunks to ChromaDB: {str(e)}")
            import traceback
            print(f"DEBUG: Error traceback: {traceback.format_exc()}")
            raise
        
        return document_id
    
    def search(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using a query embedding.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of search results with text and metadata
        """
        # Convert numpy array to list for ChromaDB
        query_embedding_list = query_embedding.tolist()
        
        # Perform search
        results = self.collection.query(
            query_embeddings=[query_embedding_list],
            n_results=top_k
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results["documents"][0])):
            formatted_results.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "id": results["ids"][0][i],
                "score": results["distances"][0][i] if "distances" in results else 0.0
            })
        
        return formatted_results
    
    def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a specific document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            List of document chunks with text and metadata
        """
        results = self.collection.get(
            where={"document_id": document_id}
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results["documents"])):
            formatted_results.append({
                "text": results["documents"][i],
                "metadata": results["metadatas"][i],
                "id": results["ids"][i]
            })
        
        return formatted_results
    
    def delete_document(self, document_id: str) -> None:
        """Delete a document and all its chunks from the vector store.
        
        Args:
            document_id: ID of the document to delete
        """
        self.collection.delete(
            where={"document_id": document_id}
        )
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection.
        
        Returns:
            Dictionary with collection statistics
        """
        # Get the number of documents in the collection
        count = self.collection.count()
        
        # Get the collection name
        collection_name = self.collection.name
        
        # Get a list of unique document IDs
        all_metadatas = self.collection.get()["metadatas"]
        document_ids = set()
        for metadata in all_metadatas:
            if "document_id" in metadata:
                document_ids.add(metadata["document_id"])
        
        return {
            "collection_name": collection_name,
            "total_chunks": count,
            "unique_documents": len(document_ids)
        } 