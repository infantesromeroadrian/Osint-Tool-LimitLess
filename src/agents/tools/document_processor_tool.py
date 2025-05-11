"""
Document processor tool for the RAG agent.
"""
from typing import Dict, List, Any, Optional
from langchain.tools import Tool
import re

class DocumentProcessorTool:
    """Tool for processing document content for the agent."""
    
    # Definir common_words como atributo de clase para que esté disponible en todos los métodos
    common_words = {"what", "who", "where", "when", "how", "why", "is", "are", 
                    "the", "a", "an", "in", "on", "at", "to", "for", "of"}
    
    def analyze_relevance(
        self, 
        query: str, 
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze relevance of retrieved documents to the query.
        
        Args:
            query: The original search query
            documents: List of retrieved documents
            
        Returns:
            Analysis results with relevance assessment
        """
        if not documents:
            return {
                "has_relevant_info": False,
                "missing_information": ["No documents retrieved"],
                "needs_refinement": True,
                "refinement_reason": "No relevant documents found"
            }
        
        # Extract query keywords
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        
        # Remove common words to focus on important terms
        query_keywords = query_words - self.common_words
        
        # Get average relevance score
        avg_relevance = sum(doc.get("relevance", 0) for doc in documents) / len(documents)
        
        # Check if documents contain the key terms
        term_matches = {}
        missing_terms = []
        
        for term in query_keywords:
            found = False
            for doc in documents:
                if term in doc.get("content", "").lower():
                    found = True
                    if term not in term_matches:
                        term_matches[term] = 0
                    term_matches[term] += 1
            
            if not found:
                missing_terms.append(term)
        
        # Determine if refinement is needed
        needs_refinement = (avg_relevance < 0.65) or (len(missing_terms) > len(query_keywords) / 2)
        
        return {
            "has_relevant_info": avg_relevance >= 0.65,
            "average_relevance": avg_relevance,
            "term_matches": term_matches,
            "missing_terms": missing_terms,
            "needs_refinement": needs_refinement,
            "refinement_reason": self._get_refinement_reason(avg_relevance, missing_terms) if needs_refinement else None
        }
    
    def _get_refinement_reason(self, avg_relevance: float, missing_terms: List[str]) -> str:
        """Generate reason for refinement."""
        reasons = []
        
        if avg_relevance < 0.65:
            reasons.append("retrieved documents have low relevance scores")
            
        if missing_terms:
            reasons.append(f"key terms not found: {', '.join(missing_terms)}")
            
        return "Query refinement needed because " + " and ".join(reasons)
    
    def refine_query(
        self, 
        original_query: str, 
        analysis: Dict[str, Any],
        retrieved_documents: List[Dict[str, Any]]
    ) -> str:
        """
        Refine the query based on analysis results.
        
        Args:
            original_query: The original search query
            analysis: Document relevance analysis
            retrieved_documents: Previously retrieved documents
            
        Returns:
            Refined query string
        """
        missing_terms = analysis.get("missing_terms", [])
        
        if not missing_terms and analysis.get("average_relevance", 0) >= 0.65:
            # No refinement needed
            return original_query
            
        # Extract relevant terms from existing documents
        context_terms = set()
        for doc in retrieved_documents:
            content = doc.get("content", "").lower()
            # Extract 1-2 word phrases
            phrases = re.findall(r'\b\w+(?:\s\w+)?\b', content)
            for phrase in phrases:
                if phrase not in self.common_words and len(phrase) > 3:
                    context_terms.add(phrase)
        
        # Select most relevant context terms (max 3)
        context_terms = list(context_terms)[:3]
        
        # Build refined query
        if missing_terms:
            # Focus on missing terms
            refined_query = f"{original_query} related to {' and '.join(missing_terms)}"
            if context_terms:
                refined_query += f" in context of {', '.join(context_terms)}"
        else:
            # Just add context terms
            refined_query = f"{original_query} specifically about {', '.join(context_terms)}"
            
        return refined_query
        
    def as_langchain_analyze_tool(self) -> Tool:
        """Convert analyze method to LangChain Tool format."""
        return Tool(
            name="analyze_document_relevance",
            description="Analyze relevance of retrieved documents to the query",
            func=self.analyze_relevance
        )
        
    def as_langchain_refine_tool(self) -> Tool:
        """Convert refine method to LangChain Tool format."""
        return Tool(
            name="refine_search_query",
            description="Refine the search query based on analysis results",
            func=self.refine_query
        ) 