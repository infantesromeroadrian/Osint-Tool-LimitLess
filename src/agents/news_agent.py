"""
News Agent implementation using LangGraph.
"""
from typing import Dict, List, Any, TypedDict, Optional, Annotated, Union, Literal
import os
from typing_extensions import TypedDict

from langchain.tools import Tool
from langgraph.graph import StateGraph, END
import operator

from src.agents.tools.news_api_tool import NewsAPITool
from src.agents.tools.response_generator_tool import ResponseGeneratorTool

# Define the agent state
class NewsAgentState(TypedDict):
    """State for the News agent workflow."""
    query: str
    original_query: str
    news_articles: List[Dict[str, Any]]
    analysis: Dict[str, Any]
    refined_query: Optional[str]
    response: Optional[Dict[str, Any]]
    chat_history: Optional[List[Dict[str, str]]]
    temperature: float
    max_tokens: int
    language: str
    days_back: int
    max_results: int

class NewsAgent:
    """News Agent that uses LangGraph to orchestrate the news retrieval and analysis process."""
    
    def __init__(self):
        """Initialize the News agent with required tools."""
        self.news_api = NewsAPITool()
        self.response_generator = ResponseGeneratorTool()
        
        # Build the graph
        self.workflow = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow.
        
        Returns:
            Compiled StateGraph
        """
        # Create a new graph
        workflow = StateGraph(NewsAgentState)
        
        # Add nodes for each step in the News process
        workflow.add_node("retrieve_news", self._retrieve_news)
        workflow.add_node("analyze_news", self._analyze_news)
        workflow.add_node("refine_query", self._refine_query)
        workflow.add_node("respond", self._generate_response)
        
        # Define the edges between nodes
        workflow.add_edge("retrieve_news", "analyze_news")
        
        # Conditional edge from analyze: either refine or respond
        workflow.add_conditional_edges(
            "analyze_news",
            self._should_refine_or_respond,
            {
                "refine": "refine_query",
                "respond": "respond"
            }
        )
        
        # From refine, go back to retrieve
        workflow.add_edge("refine_query", "retrieve_news")
        
        # Response is the end state
        workflow.add_edge("respond", END)
        
        # Set the entry point
        workflow.set_entry_point("retrieve_news")
        
        # Compile the graph
        return workflow.compile()
    
    def _retrieve_news(self, state: NewsAgentState) -> Dict[str, Any]:
        """Retrieve relevant news articles for the query.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with retrieved news articles
        """
        query = state["query"]
        max_results = state.get("max_results", 10)
        days_back = state.get("days_back", 7)
        language = state.get("language", "en")
        
        # Retrieve news articles
        news_articles = self.news_api.search_news(
            query=query,
            max_results=max_results,
            days_back=days_back,
            language=language
        )
        
        return {"news_articles": news_articles}
    
    def _analyze_news(self, state: NewsAgentState) -> Dict[str, Any]:
        """Analyze retrieved news articles for relevance.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with news analysis
        """
        query = state["query"]
        news_articles = state["news_articles"]
        
        # Check if we have articles
        if not news_articles:
            return {
                "analysis": {
                    "has_relevant_info": False,
                    "missing_information": ["No news articles found"],
                    "needs_refinement": True,
                    "refinement_reason": "No relevant news articles found"
                }
            }
        
        # Count articles with actual content
        articles_with_content = sum(1 for article in news_articles if article.get("content") and article.get("content") != "No content available")
        
        # Check if we have error articles
        has_errors = any(article.get("source") == "Error" for article in news_articles)
        
        # Analyze recency of articles
        from datetime import datetime, timedelta
        recent_articles = 0
        for article in news_articles:
            if article.get("published_at"):
                try:
                    pub_date = datetime.fromisoformat(article["published_at"].replace("Z", "+00:00"))
                    if datetime.now() - pub_date <= timedelta(days=3):
                        recent_articles += 1
                except (ValueError, TypeError):
                    pass
        
        # Determine if refinement is needed
        needs_refinement = has_errors or articles_with_content < 3
        
        return {
            "analysis": {
                "has_relevant_info": articles_with_content >= 3,
                "total_articles": len(news_articles),
                "articles_with_content": articles_with_content,
                "recent_articles": recent_articles,
                "has_errors": has_errors,
                "needs_refinement": needs_refinement,
                "refinement_reason": self._get_refinement_reason(has_errors, articles_with_content) if needs_refinement else None
            }
        }
    
    def _get_refinement_reason(self, has_errors: bool, articles_with_content: int) -> str:
        """Generate reason for refinement."""
        reasons = []
        
        if has_errors:
            reasons.append("API errors occurred during news retrieval")
            
        if articles_with_content < 3:
            reasons.append(f"only found {articles_with_content} articles with content")
            
        return "Query refinement needed because " + " and ".join(reasons)
    
    def _should_refine_or_respond(self, state: NewsAgentState) -> Literal["refine", "respond"]:
        """Determine whether to refine the query or respond.
        
        Args:
            state: Current agent state
            
        Returns:
            Next node to transition to
        """
        analysis = state["analysis"]
        
        # If refinement is needed (currently only does one refinement)
        if analysis.get("needs_refinement", False) and state.get("refined_query") is None:
            return "refine"
        
        # Otherwise, respond with what we have
        return "respond"
    
    def _refine_query(self, state: NewsAgentState) -> Dict[str, Any]:
        """Refine the query to get better news results.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with refined query
        """
        original_query = state.get("original_query", state["query"])
        
        # Simple query expansion with more specific terms
        # In a production system, we would use the LLM for this
        refined_query = f"{original_query} latest news updates report"
        
        return {
            "query": refined_query,
            "refined_query": refined_query
        }
    
    def _generate_response(self, state: NewsAgentState) -> Dict[str, Any]:
        """Generate the final response from news articles.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with generated response
        """
        query = state.get("original_query", state["query"])
        news_articles = state["news_articles"]
        analysis = state["analysis"]
        chat_history = state.get("chat_history")
        temperature = state.get("temperature", 0.7)
        max_tokens = state.get("max_tokens", 500)
        
        # Check if we have articles
        if news_articles:
            # Generate answer summarizing news
            response = self.response_generator.generate_news_summary(
                query=query,
                news_articles=news_articles,
                analysis=analysis,
                temperature=temperature,
                max_tokens=max_tokens,
                chat_history=chat_history
            )
        else:
            # Generate fallback response
            response = {
                "answer": "I couldn't find any recent news articles related to your query. Try refining your search or check back later as more news becomes available.",
                "confidence": "low"
            }
        
        return {"response": response}
    
    def query(
        self, 
        query: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        days_back: int = 7,
        max_results: int = 10,
        language: str = "en",
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Run the News agent to answer a query with recent news.
        
        Args:
            query: User's query
            temperature: Temperature for LLM
            max_tokens: Maximum tokens for response
            days_back: Number of days to look back for news
            max_results: Maximum number of news articles to retrieve
            language: Language for news articles
            chat_history: Optional chat history
            
        Returns:
            Response from the agent
        """
        # Initialize state
        initial_state: NewsAgentState = {
            "query": query,
            "original_query": query,
            "news_articles": [],
            "analysis": {},
            "refined_query": None,
            "response": None,
            "chat_history": chat_history,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "language": language,
            "days_back": days_back,
            "max_results": max_results
        }
        
        # Execute the graph
        result = self.workflow.invoke(initial_state)
        
        # Return the final response
        return {
            "answer": result["response"]["answer"],
            "sources": [
                {
                    "title": article.get("title", "No title"),
                    "content": article.get("description", article.get("content", "No content")),
                    "document": article.get("source", "Unknown"),
                    "url": article.get("url", ""),
                    "published_at": article.get("published_at", ""),
                    "relevance": article.get("relevance", 1.0)
                }
                for article in result["news_articles"]
            ],
            "query": query,
            "refined_query": result.get("refined_query"),
            "confidence": result["response"].get("confidence", "medium")
        } 