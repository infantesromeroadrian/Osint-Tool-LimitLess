"""
News API tool for retrieving recent news articles.
"""
from typing import Dict, List, Any, Optional
import os
import requests
from datetime import datetime, timedelta
from langchain.tools import Tool

class NewsAPITool:
    """Tool for retrieving news articles from the Open News API."""
    
    def __init__(self):
        """Initialize the News API tool."""
        self.api_key = os.environ.get("OPENNEWS_API_KEY")
        if not self.api_key:
            raise ValueError("OPENNEWS_API_KEY environment variable not found")
        self.base_url = "https://newsapi.org/v2"
    
    def search_news(
        self, 
        query: str, 
        days_back: int = 7,
        max_results: int = 10,
        language: str = "en",
        sort_by: str = "relevancy"  # Options: relevancy, popularity, publishedAt
    ) -> List[Dict[str, Any]]:
        """
        Search for news articles related to a query.
        
        Args:
            query: The search query for news articles
            days_back: How many days back to search for news
            max_results: Maximum number of results to return
            language: Language of news articles (e.g., 'en', 'es')
            sort_by: How to sort the results
            
        Returns:
            List of news article data
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Format dates for API
        from_date = start_date.strftime("%Y-%m-%d")
        to_date = end_date.strftime("%Y-%m-%d")
        
        # Build API endpoint
        endpoint = f"{self.base_url}/everything"
        
        # Make API request
        try:
            response = requests.get(
                endpoint,
                params={
                    "q": query,
                    "apiKey": self.api_key,
                    "from": from_date,
                    "to": to_date,
                    "language": language,
                    "sortBy": sort_by,
                    "pageSize": max_results
                },
                timeout=10
            )
            
            # Check for successful response
            if response.status_code == 200:
                data = response.json()
                
                # Process news articles
                articles = []
                for article in data.get("articles", [])[:max_results]:
                    articles.append({
                        "title": article.get("title", "No title"),
                        "description": article.get("description", "No description"),
                        "content": article.get("content", "No content available"),
                        "url": article.get("url", ""),
                        "source": article.get("source", {}).get("name", "Unknown source"),
                        "published_at": article.get("publishedAt", ""),
                        "relevance": 1.0  # Default relevance to match document format
                    })
                
                return articles
            else:
                # Handle API errors
                error_msg = f"News API error: {response.status_code} - {response.text}"
                print(error_msg)
                return [{
                    "title": "API Error",
                    "description": error_msg,
                    "content": "Could not retrieve news articles due to API error",
                    "url": "",
                    "source": "Error",
                    "published_at": "",
                    "relevance": 0.0
                }]
                
        except Exception as e:
            # Handle request exceptions
            error_msg = f"Error fetching news: {str(e)}"
            print(error_msg)
            return [{
                "title": "Request Error",
                "description": error_msg,
                "content": "Could not connect to news service",
                "url": "",
                "source": "Error",
                "published_at": "",
                "relevance": 0.0
            }]
    
    def get_top_headlines(
        self,
        category: Optional[str] = None,
        country: str = "us",
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top headlines, optionally filtered by category and country.
        
        Args:
            category: Optional category (business, entertainment, general, health, science, sports, technology)
            country: Country code (e.g., 'us', 'gb')
            max_results: Maximum number of results to return
            
        Returns:
            List of headline article data
        """
        # Build API endpoint
        endpoint = f"{self.base_url}/top-headlines"
        
        # Prepare parameters
        params = {
            "apiKey": self.api_key,
            "country": country,
            "pageSize": max_results
        }
        
        # Add category if provided
        if category:
            params["category"] = category
        
        # Make API request
        try:
            response = requests.get(
                endpoint,
                params=params,
                timeout=10
            )
            
            # Check for successful response
            if response.status_code == 200:
                data = response.json()
                
                # Process news articles
                articles = []
                for article in data.get("articles", [])[:max_results]:
                    articles.append({
                        "title": article.get("title", "No title"),
                        "description": article.get("description", "No description"),
                        "content": article.get("content", "No content available"),
                        "url": article.get("url", ""),
                        "source": article.get("source", {}).get("name", "Unknown source"),
                        "published_at": article.get("publishedAt", ""),
                        "relevance": 1.0  # Default relevance to match document format
                    })
                
                return articles
            else:
                # Handle API errors
                error_msg = f"News API error: {response.status_code} - {response.text}"
                print(error_msg)
                return [{
                    "title": "API Error",
                    "description": error_msg,
                    "content": "Could not retrieve headlines due to API error",
                    "url": "",
                    "source": "Error",
                    "published_at": "",
                    "relevance": 0.0
                }]
                
        except Exception as e:
            # Handle request exceptions
            error_msg = f"Error fetching headlines: {str(e)}"
            print(error_msg)
            return [{
                "title": "Request Error",
                "description": error_msg,
                "content": "Could not connect to news service",
                "url": "",
                "source": "Error",
                "published_at": "",
                "relevance": 0.0
            }]
    
    def as_langchain_search_tool(self) -> Tool:
        """Convert search method to LangChain Tool format."""
        return Tool(
            name="search_news",
            description="Search for recent news articles on a specific topic",
            func=self.search_news
        )
    
    def as_langchain_headlines_tool(self) -> Tool:
        """Convert headlines method to LangChain Tool format."""
        return Tool(
            name="get_top_headlines",
            description="Get top news headlines, optionally by category and country",
            func=self.get_top_headlines
        ) 