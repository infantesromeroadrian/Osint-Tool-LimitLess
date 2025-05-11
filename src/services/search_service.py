import os
import re
from typing import Dict, List, Any, Optional
from services.services import BaseService
from utils.vector_store import VectorStore
from utils.embedding_generator import EmbeddingGenerator
from utils.llm_interface import LLMInterface
from src.agents.rag_agent import RAGAgent
from src.agents.multi_agent import MultiAgent

class SearchService(BaseService):
    """Service for searching and retrieving intelligence with RAG."""
    
    def __init__(self):
        """Initialize search service with required dependencies."""
        self.vector_store = VectorStore()
        self.embedding_generator = EmbeddingGenerator()
        self.llm = LLMInterface(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Initialize agents
        self.rag_agent = RAGAgent()
        self.multi_agent = MultiAgent()
    
    def search(
        self, 
        query: str, 
        temperature: float = 0.7,
        max_tokens: int = 500,
        top_k: int = 5,
        chat_history: Optional[List[Dict[str, str]]] = None,
        use_agent: bool = True,  # Flag to use the advanced RAG agent
        use_news: bool = True    # Flag to use the news agent together with RAG
    ) -> Dict[str, Any]:
        """Search intelligence database using RAG.
        
        Args:
            query: The user's intelligence query
            temperature: Temperature for LLM response
            max_tokens: Maximum tokens in response
            top_k: Number of relevant sources to retrieve
            chat_history: Optional list of previous chat messages
            use_agent: Whether to use the advanced RAG agent
            use_news: Whether to use news data alongside documents
            
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
            elif not has_documents and chat_history is None and not use_news:
                return {
                    "answer": "I don't have any intelligence documents to search yet. Please upload some documents in the 'Upload Documents' tab first.",
                    "sources": [],
                    "query": query
                }
            
            # Use the Multi Agent if both agent and news flags are enabled
            if use_agent and use_news:
                multi_response = self.multi_agent.query(
                    query=query,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_k=top_k,
                    chat_history=chat_history,
                    days_back=7  # Default to 7 days for news, could be a parameter
                )
                
                # Format sources for display
                formatted_sources = self._format_multi_sources(multi_response["sources"])
                
                # Indicate if queries were refined
                refined_info = ""
                rag_refined = multi_response.get("rag_refined_query")
                news_refined = multi_response.get("news_refined_query")
                
                if (rag_refined and rag_refined != query) or (news_refined and news_refined != query):
                    refined_info = "\n\n(Note: I refined your query to get better results"
                    if rag_refined and rag_refined != query:
                        refined_info += f", RAG query: '{rag_refined}'"
                    if news_refined and news_refined != query:
                        refined_info += f", News query: '{news_refined}'"
                    refined_info += ")"
                
                return {
                    "answer": multi_response["answer"] + refined_info,
                    "sources": formatted_sources,
                    "query": query,
                    "confidence": multi_response.get("confidence", "medium"),
                    "primary_source": multi_response.get("primary_source", "combined"),
                    "using_agent": True,
                    "using_news": True
                }
            
            # Use only the RAG agent if only the agent flag is enabled
            elif use_agent and has_documents:
                agent_response = self.rag_agent.query(
                    query=query,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_k=top_k,
                    chat_history=chat_history
                )
                
                # Format sources for display
                sources = self._format_sources(agent_response["sources"])
                
                # Indicate if query was refined
                refined_info = ""
                if agent_response.get("refined_query") and agent_response.get("refined_query") != query:
                    refined_info = f"\n\n(Note: I refined your query to: '{agent_response['refined_query']}')"
                    
                return {
                    "answer": agent_response["answer"] + refined_info,
                    "sources": sources,
                    "query": query,
                    "confidence": agent_response.get("confidence", "medium"),
                    "using_agent": True,
                    "using_news": False
                }
            
            # Legacy RAG approach (original implementation) if not using agent
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
                "query": query,
                "using_agent": False,
                "using_news": False
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
    
    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into context.
        
        Args:
            chunks: Retrieved document chunks
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            # Format chunk with document reference
            chunk_text = f"Document {i+1}: {chunk.get('metadata', {}).get('filename', 'Unknown')}\n\n"
            chunk_text += chunk.get("text", "")
            
            context_parts.append(chunk_text)
        
        return "\n\n".join(context_parts)
    
    def _format_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format sources for display in UI.
        
        Args:
            chunks: Retrieved document chunks
            
        Returns:
            Formatted source list
        """
        sources = []
        
        for i, chunk in enumerate(chunks):
            if isinstance(chunk, dict):
                # For RAG agent sources that may have different format
                source = {
                    "title": f"Source {i+1}",
                    "content": chunk.get("content", chunk.get("text", "")),
                    "document": chunk.get("document", chunk.get("metadata", {}).get("filename", "Unknown")),
                    "relevance": chunk.get("relevance", chunk.get("score", 0.0))
                }
                sources.append(source)
            else:
                # Fallback for other formats
                sources.append({
                    "title": f"Source {i+1}",
                    "content": "Content not available",
                    "document": "Unknown",
                    "relevance": 0.0
                })
        
        return sources
    
    def _format_multi_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format multi-agent sources for display in UI.
        
        Args:
            sources: Combined sources from multiple agents
            
        Returns:
            Formatted source list
        """
        formatted_sources = []
        
        for i, source in enumerate(sources):
            source_type = source.get("type", "unknown")
            
            if source_type == "document":
                # Format document source
                formatted_source = {
                    "title": source.get("title", f"Document {i+1}"),
                    "content": source.get("content", ""),
                    "document": source.get("document", "Unknown"),
                    "relevance": source.get("relevance", 0.0),
                    "source_type": "Document"
                }
            elif source_type == "news":
                # Format news source
                formatted_source = {
                    "title": source.get("title", f"News {i+1}"),
                    "content": source.get("content", ""),
                    "document": source.get("document", "Unknown Source"),
                    "url": source.get("url", ""),
                    "published_at": source.get("published_at", ""),
                    "relevance": source.get("relevance", 0.0),
                    "source_type": "News"
                }
            else:
                # Fallback for unknown source types
                formatted_source = {
                    "title": f"Source {i+1}",
                    "content": source.get("content", "Content not available"),
                    "document": source.get("document", "Unknown"),
                    "relevance": source.get("relevance", 0.0),
                    "source_type": "Unknown"
                }
            
            formatted_sources.append(formatted_source)
        
        return formatted_sources
    
    def _local_text_analysis(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """Basic text analysis as fallback when LLM unavailable.
        
        Args:
            query: User's query
            chunks: Retrieved document chunks
            
        Returns:
            Simple analysis result
        """
        combined_text = " ".join([chunk.get("text", "") for chunk in chunks])
        
        # Extract query terms (excluding common words)
        common_words = {"what", "who", "where", "when", "how", "why", "is", "are", 
                      "the", "a", "an", "in", "on", "at", "to", "for", "of"}
        query_words = set(re.findall(r'\b\w+\b', query.lower())) - common_words
        
        # Find sentences with query terms
        sentences = re.split(r'(?<=[.!?])\s+', combined_text)
        relevant_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for word in query_words:
                if word in sentence_lower:
                    relevant_sentences.append(sentence)
                    break
        
        if relevant_sentences:
            # Return the relevant sentences (max 5)
            response = "Based on the documents, I found this information:\n\n"
            response += " ".join(relevant_sentences[:5])
            response += "\n\n(Note: This is a simplified analysis. The AI service may be temporarily unavailable.)"
            return response
        else:
            return "I found some documents that might be relevant, but couldn't generate a specific answer. Please try again later when the AI service is available." 