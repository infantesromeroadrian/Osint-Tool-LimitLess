import os
import re
from typing import Dict, List, Any, Optional
from services.services import BaseService
from utils.vector_store import VectorStore
from utils.embedding_generator import EmbeddingGenerator
from utils.llm_interface import LLMInterface

class SearchService(BaseService):
    """Service for searching and retrieving intelligence with RAG."""
    
    def __init__(self):
        """Initialize search service with required dependencies."""
        self.vector_store = VectorStore()
        self.embedding_generator = EmbeddingGenerator()
        self.llm = LLMInterface(api_key=os.environ.get("OPENAI_API_KEY"))
    
    def search(
        self, 
        query: str, 
        temperature: float = 0.7,
        max_tokens: int = 500,
        top_k: int = 5,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Search intelligence database using RAG.
        
        Args:
            query: The user's intelligence query
            temperature: Temperature for LLM response
            max_tokens: Maximum tokens in response
            top_k: Number of relevant sources to retrieve
            chat_history: Optional list of previous chat messages
            
        Returns:
            Dictionary with search results and sources
        """
        try:
            # Check if database has documents
            stats = self.vector_store.get_collection_stats()
            has_documents = stats["total_chunks"] > 0
            
            # If no documents but in chat mode, fallback to direct AI conversation
            if not has_documents and chat_history is not None:
                # Generate response using just the LLM without document context
                response = self.llm.generate_general_response(
                    query=query,
                    chat_history=chat_history,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # Include a note about missing documents in first response only
                if len(chat_history) < 2:  # Only for first exchange
                    note = "Note: No documents have been uploaded yet. I'm responding based on my general knowledge. For document-specific information, please upload documents in the 'Upload Documents' tab."
                    response = f"{response}\n\n{note}"
                
                return {
                    "answer": response,
                    "sources": [],
                    "query": query,
                    "using_general_ai": True
                }
            
            # For standard search without documents, return guidance message
            elif not has_documents and chat_history is None:
                return {
                    "answer": "I don't have any intelligence documents to search yet. Please upload some documents in the 'Upload Documents' tab first.",
                    "sources": [],
                    "query": query
                }
            
            # Normal RAG-based search when documents are available
            # Generate embedding for query
            query_embedding = self.embedding_generator.generate_query_embedding(
                query, 
                model_name="all-MiniLM-L6-v2"
            )
            
            # Retrieve relevant chunks from vector store
            relevant_chunks = self.vector_store.search(
                query_embedding,
                top_k=top_k
            )
            
            # Format context for the LLM
            context = self._format_context(relevant_chunks)
            
            try:
                # Attempt to generate answer with LLM using RAG
                if chat_history:
                    # Use the chat-aware generation method if history is provided
                    answer = self.llm.generate_chat_response(
                        query=query,
                        context=context,
                        chat_history=chat_history,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                else:
                    # Use the standard generation method for single queries
                    answer = self.llm.generate_answer(
                        query=query,
                        context=context,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
            except Exception as e:
                print(f"LLM API error: {str(e)}, using local fallback")
                # Use local fallback if LLM API fails
                answer = self._local_text_analysis(query, relevant_chunks)
            
            # Format sources for display
            sources = self._format_sources(relevant_chunks)
            
            return {
                "answer": answer,
                "sources": sources,
                "query": query
            }
            
        except Exception as e:
            # Log the actual error for debugging
            print(f"Error in search service: {str(e)}")
            
            # Return a user-friendly error message
            return {
                "error": str(e),
                "answer": "Sorry, I encountered an error while searching for intelligence data. Please try again or upload some documents if you haven't already.",
                "sources": [],
                "query": query
            }
    
    def _local_text_analysis(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """Generate a simple answer locally when LLM API is unavailable.
        
        Args:
            query: The user's query
            chunks: List of retrieved document chunks
            
        Returns:
            Generated answer text
        """
        if not chunks:
            return "No relevant information found in the documents."
        
        # Simple text extraction based on keyword matching
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        
        # Remove common words to focus on important terms
        common_words = {"what", "who", "where", "when", "how", "why", "is", "are", "the", "a", "an", "in", "on", "at", "to", "for", "of"}
        query_keywords = query_words - common_words
        
        # If no meaningful keywords left, use simple summarization
        if not query_keywords:
            return "Found relevant information in the documents. Please check the sources below."
        
        # Look for sentences in chunks that match query keywords
        response_parts = []
        
        # Check if it's asking for a specific named entity
        name_patterns = [
            (r'(?:who|what)\s+(?:is|are)\s+(?:the|a)?\s*(\w+)', "Extracting information about {}..."),
            (r'(?:name|identify)\s+(?:of|the)?\s*(\w+)', "The name you're looking for might be {}..."),
            (r'(?:which|what)\s+(\w+)', "According to the documents, {} is mentioned..."),
        ]
        
        name_matches = []
        for pattern, template in name_patterns:
            matches = re.findall(pattern, query.lower())
            for match in matches:
                if match and match not in common_words:
                    name_matches.append(match)
        
        # Check if any matches were found
        if name_matches:
            for chunk in chunks:
                text = chunk["text"].lower()
                for name in name_matches:
                    if name in text:
                        sentences = re.split(r'[.!?]', chunk["text"])
                        for sentence in sentences:
                            if name.lower() in sentence.lower():
                                response_parts.append(sentence.strip())
        
        # If no specific matches, extract sentences with query keywords
        if not response_parts:
            for chunk in chunks:
                text = chunk["text"]
                sentences = re.split(r'[.!?]', text)
                for sentence in sentences:
                    if any(keyword in sentence.lower() for keyword in query_keywords):
                        response_parts.append(sentence.strip())
        
        if response_parts:
            # Combine unique sentences
            unique_responses = list(set(response_parts))
            return " ".join(unique_responses[:3])  # Limit to 3 sentences for clarity
        else:
            # Fallback to returning the most relevant chunk
            return chunks[0]["text"]
    
    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into context for the LLM.
        
        Args:
            chunks: List of retrieved document chunks
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            context_parts.append(f"[Document {i+1}]: {chunk['text']}")
        
        return "\n\n".join(context_parts)
    
    def _format_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format sources for display in the UI.
        
        Args:
            chunks: List of retrieved document chunks
            
        Returns:
            Formatted list of sources
        """
        sources = []
        
        for i, chunk in enumerate(chunks):
            sources.append({
                "title": f"Excerpt {i+1}",
                "content": chunk["text"],
                "document": chunk["metadata"]["filename"] if "filename" in chunk["metadata"] else chunk["metadata"].get("document_name", "Unknown"),
                "relevance": chunk["score"]
            })
        
        return sources 