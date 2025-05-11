"""
Multi-Agent implementation that combines RAG and News agents.
"""
from typing import Dict, List, Any, Optional, Tuple, Union
import os

from src.agents.rag_agent import RAGAgent
from src.agents.news_agent import NewsAgent
from utils.llm_interface import LLMInterface

class MultiAgent:
    """Agent that combines different specialized agents for better responses."""
    
    def __init__(self):
        """Initialize the multi-agent with its component agents."""
        self.rag_agent = RAGAgent()  # Agent for document-based answers
        self.news_agent = NewsAgent()  # Agent for news-based answers
        self.llm = LLMInterface(api_key=os.environ.get("OPENAI_API_KEY"))
    
    def query(
        self, 
        query: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        top_k: int = 5,
        chat_history: Optional[List[Dict[str, str]]] = None,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """Query multiple agents and combine their responses.
        
        Args:
            query: User's query
            temperature: Temperature for LLM
            max_tokens: Maximum tokens for response
            top_k: Number of documents/articles to retrieve
            chat_history: Optional chat history for conversation
            days_back: Number of days to look back for news
            
        Returns:
            Combined response
        """
        # Query both agents asynchronously (in production, this would be properly parallelized)
        rag_response = self.rag_agent.query(
            query=query,
            temperature=temperature,
            max_tokens=max_tokens,
            top_k=top_k,
            chat_history=chat_history
        )
        
        news_response = self.news_agent.query(
            query=query,
            temperature=temperature,
            max_tokens=max_tokens,
            max_results=top_k,
            days_back=days_back,
            chat_history=chat_history
        )
        
        # Check which agent produced higher confidence results
        rag_confidence = self._confidence_score(rag_response.get("confidence", "low"))
        news_confidence = self._confidence_score(news_response.get("confidence", "low"))
        
        # Combine sources
        combined_sources = []
        
        # Add document sources
        if rag_response.get("sources"):
            for source in rag_response["sources"]:
                combined_sources.append({
                    "type": "document",
                    "title": source.get("title", "Document"),
                    "content": source.get("content", ""),
                    "document": source.get("document", "Unknown"),
                    "relevance": source.get("relevance", 0.0)
                })
        
        # Add news sources
        if news_response.get("sources"):
            for source in news_response["sources"]:
                combined_sources.append({
                    "type": "news",
                    "title": source.get("title", "News Article"),
                    "content": source.get("content", ""),
                    "document": source.get("document", "Unknown Source"),
                    "url": source.get("url", ""),
                    "published_at": source.get("published_at", ""),
                    "relevance": source.get("relevance", 0.0)
                })
        
        # If both agents gave high confidence, combine their answers
        if rag_confidence >= 2 and news_confidence >= 2:
            # Combine the answers with the LLM
            combined_answer = self._combine_answers(
                query=query,
                rag_answer=rag_response.get("answer", ""),
                news_answer=news_response.get("answer", ""),
                temperature=temperature,
                max_tokens=max_tokens
            )
            confidence = "high"
            primary_source = "combined"
        elif rag_confidence > news_confidence:
            # Use RAG answer as it has higher confidence
            combined_answer = rag_response.get("answer", "")
            confidence = rag_response.get("confidence", "medium")
            primary_source = "documents"
        else:
            # Use News answer as it has higher confidence
            combined_answer = news_response.get("answer", "")
            confidence = news_response.get("confidence", "medium")
            primary_source = "news"
        
        # Return the combined result
        return {
            "answer": combined_answer,
            "sources": combined_sources,
            "query": query,
            "confidence": confidence,
            "primary_source": primary_source,
            "rag_refined_query": rag_response.get("refined_query"),
            "news_refined_query": news_response.get("refined_query")
        }
    
    def _confidence_score(self, confidence: str) -> int:
        """Convert confidence string to numerical score.
        
        Args:
            confidence: Confidence level as string
            
        Returns:
            Numerical score (1-3)
        """
        if confidence.lower() == "high":
            return 3
        elif confidence.lower() == "medium":
            return 2
        else:
            return 1
    
    def _combine_answers(
        self,
        query: str,
        rag_answer: str,
        news_answer: str,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Combine answers from different agents using the LLM.
        
        Args:
            query: Original user query
            rag_answer: Answer from RAG agent
            news_answer: Answer from News agent
            temperature: Temperature for LLM
            max_tokens: Maximum tokens for combined response
            
        Returns:
            Combined answer text
        """
        # Create a prompt for combining the answers
        prompt = f"""
You are an intelligence analyst tasked with combining information from two sources to provide the most comprehensive answer.

User Query: {query}

Source 1 (Document Analysis): 
{rag_answer}

Source 2 (Recent News Analysis):
{news_answer}

Please combine these perspectives into a comprehensive response that addresses the user's query. 
Highlight where the information from documents and recent news complement or contradict each other.
Be sure to maintain factual accuracy and clearly indicate the source of information when appropriate.
Your response should be well-structured, balanced, and contain the most relevant information from both sources.
"""
        
        # Use the LLM to combine the answers
        combined_answer = self.llm.generate_answer(
            query=prompt,
            context="",  # No additional context needed
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return combined_answer 