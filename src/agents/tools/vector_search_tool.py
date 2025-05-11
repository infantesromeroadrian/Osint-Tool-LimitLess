"""
Vector search tool for the RAG agent.
"""
from typing import Dict, List, Any, Optional
from langchain.tools import Tool
from utils.vector_store import VectorStore
from utils.embedding_generator import EmbeddingGenerator
from utils.case_path_resolver import CasePathResolver

class VectorSearchTool:
    """Tool for searching the vector database."""
    
    def __init__(self):
        """Initialize the vector search tool."""
        self.vector_store = VectorStore()
        self.embedding_generator = EmbeddingGenerator()
        self.case_resolver = CasePathResolver()
        
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents in the vector store.
        
        Args:
            query: The search query
            top_k: Number of results to return
            threshold: Minimum relevance score threshold
            
        Returns:
            List of relevant document chunks with metadata
        """
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_query_embedding(
            query, 
            model_name="all-MiniLM-L6-v2"
        )
        
        # Retrieve relevant chunks from vector store
        relevant_chunks = self.vector_store.search(
            query_embedding,
            top_k=top_k
        )
        
        # Filter by threshold if specified
        if threshold < 1.0:
            relevant_chunks = [
                chunk for chunk in relevant_chunks 
                if chunk["score"] >= threshold
            ]
            
        # Format results with additional metadata
        results = []
        for chunk in relevant_chunks:
            # Add filename and other useful metadata
            results.append({
                "content": chunk["text"],
                "metadata": chunk["metadata"],
                "relevance": chunk["score"],
                "document": chunk["metadata"].get("filename", "Unknown"),
                "chunk_id": chunk["id"]
            })
            
        return results
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database collection."""
        return self.vector_store.get_collection_stats()
        
    def as_langchain_tool(self) -> Tool:
        """Convert to LangChain Tool format."""
        return Tool(
            name="vector_search",
            description="Search for relevant documents using vector similarity",
            func=self.search
        ) 