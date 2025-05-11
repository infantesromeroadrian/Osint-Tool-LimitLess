"""
Response generator tool for the RAG agent.
"""
from typing import Dict, List, Any, Optional
import os
from langchain.tools import Tool
from utils.llm_interface import LLMInterface

class ResponseGeneratorTool:
    """Tool for generating responses based on retrieved content."""
    
    def __init__(self):
        """Initialize the response generator tool."""
        self.llm = LLMInterface(api_key=os.environ.get("OPENAI_API_KEY"))
    
    def format_context(self, documents: List[Dict[str, Any]]) -> str:
        """Format retrieved documents into context.
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, doc in enumerate(documents):
            # Get document content and metadata
            content = doc.get("content", "")
            doc_name = doc.get("document", doc.get("metadata", {}).get("filename", f"Document {i+1}"))
            
            # Format with document name
            context_parts.append(f"[{doc_name}]: {content}")
        
        return "\n\n".join(context_parts)
    
    def format_news_context(self, news_articles: List[Dict[str, Any]]) -> str:
        """Format news articles into context.
        
        Args:
            news_articles: List of news articles
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, article in enumerate(news_articles):
            # Get article content and metadata
            title = article.get("title", f"Article {i+1}")
            content = article.get("content", "No content available")
            description = article.get("description", "")
            source = article.get("source", "Unknown source")
            published_at = article.get("published_at", "")
            url = article.get("url", "")
            
            # Use description if content is not available or too short
            if content == "No content available" or len(content) < len(description):
                content = description
            
            # Format article with metadata
            article_text = f"TITLE: {title}\n"
            article_text += f"SOURCE: {source}\n"
            if published_at:
                article_text += f"DATE: {published_at}\n"
            article_text += f"CONTENT: {content}\n"
            if url:
                article_text += f"URL: {url}"
            
            context_parts.append(article_text)
        
        return "\n\n" + "\n\n".join(context_parts)
    
    def generate_answer(
        self, 
        query: str,
        documents: List[Dict[str, Any]],
        analysis: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: int = 500,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Generate an answer using the LLM with RAG.
        
        Args:
            query: User's query
            documents: Retrieved relevant documents
            analysis: Document relevance analysis
            temperature: Temperature setting for LLM
            max_tokens: Maximum tokens for response
            chat_history: Optional chat history for conversation
            
        Returns:
            Generated answer with metadata
        """
        # Format context from documents
        context = self.format_context(documents)
        
        # Different generation based on chat history
        if chat_history:
            # Use conversational endpoint
            answer = self.llm.generate_chat_response(
                query=query,
                context=context,
                chat_history=chat_history,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            # Use standard endpoint
            answer = self.llm.generate_answer(
                query=query,
                context=context,
                temperature=temperature,
                max_tokens=max_tokens
            )
        
        # Add confidence and source attribution
        return {
            "answer": answer,
            "has_context": bool(documents),
            "sources": [doc.get("document", "Unknown") for doc in documents],
            "confidence": "high" if analysis.get("has_relevant_info", False) else "medium",
            "missing_information": analysis.get("missing_terms", [])
        }
    
    def generate_news_summary(
        self, 
        query: str,
        news_articles: List[Dict[str, Any]],
        analysis: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: int = 500,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Generate a news summary using the LLM.
        
        Args:
            query: User's query
            news_articles: Retrieved news articles
            analysis: News articles analysis
            temperature: Temperature setting for LLM
            max_tokens: Maximum tokens for response
            chat_history: Optional chat history for conversation
            
        Returns:
            Generated answer with metadata
        """
        # Format news context
        news_context = self.format_news_context(news_articles)
        
        # Create a special prompt for news summarization
        prompt = f"""
You are analyzing recent news articles to answer the user's query. 
Use only the information from the provided news articles to answer the query.
When citing information, mention the source.

USER QUERY: {query}

NEWS ARTICLES:
{news_context}

Please provide a comprehensive answer based solely on these news articles. 
If the articles don't contain sufficient information to answer the query completely, acknowledge the limitations.
"""
        
        # Different generation based on chat history
        if chat_history:
            # Create message list starting with system prompt
            messages = [{"role": "system", "content": "You are a news analyst providing insights based on recent news articles."}]
            
            # Add chat history (limit to last 5 messages to prevent token overflow)
            for message in chat_history[-5:]:
                messages.append({"role": message["role"], "content": message["content"]})
            
            # Add current prompt as user message
            messages.append({"role": "user", "content": prompt})
            
            # Use the OpenAI chat API through our LLM interface
            response = self.llm.client.chat.completions.create(
                model="gpt-4-0125-preview",  # Use a suitable model
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract the assistant's response
            answer = response.choices[0].message.content
        else:
            # For non-chat interactions, use standard completion
            answer = self.llm.generate_answer(
                query=prompt,  # Using our prompt as the query
                context="",  # Context is already in the prompt
                temperature=temperature,
                max_tokens=max_tokens,
                model="gpt-4-0125-preview"  # Use a suitable model
            )
        
        # Add confidence level based on analysis
        confidence = "high" if analysis.get("has_relevant_info", True) and analysis.get("articles_with_content", 0) > 3 else "medium"
        
        # Add source attribution to response
        sources = []
        for article in news_articles:
            if article.get("source") != "Error":
                sources.append(article.get("source", "Unknown source"))
        
        # Remove duplicates
        unique_sources = list(set(sources))
        
        # Add confidence and sources to response
        return {
            "answer": answer,
            "has_context": bool(news_articles),
            "sources": unique_sources,
            "confidence": confidence,
            "article_count": len(news_articles)
        }
    
    def generate_fallback_response(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Generate a fallback response when no documents are available.
        
        Args:
            query: User's query
            chat_history: Optional chat history for conversation
            
        Returns:
            Generated fallback response
        """
        if chat_history:
            # Use the general response for chat
            response = self.llm.generate_general_response(
                query=query,
                chat_history=chat_history,
                temperature=0.7,
                max_tokens=500
            )
        else:
            # Standard message for first-time queries
            response = ("I don't have specific information about that in my knowledge base. "
                       "Please upload relevant documents or try a different query.")
        
        return {
            "answer": response,
            "has_context": False,
            "sources": [],
            "confidence": "low",
            "missing_information": ["No relevant documents found"]
        }
        
    def as_langchain_tool(self) -> Tool:
        """Convert to LangChain Tool format."""
        return Tool(
            name="generate_response",
            description="Generate a response based on retrieved documents",
            func=self.generate_answer
        )
        
    def as_langchain_fallback_tool(self) -> Tool:
        """Convert fallback method to LangChain Tool format."""
        return Tool(
            name="generate_fallback_response",
            description="Generate a fallback response when no documents are available",
            func=self.generate_fallback_response
        )
        
    def as_langchain_news_tool(self) -> Tool:
        """Convert news summary method to LangChain Tool format."""
        return Tool(
            name="generate_news_summary",
            description="Generate a news summary based on retrieved news articles",
            func=self.generate_news_summary
        ) 