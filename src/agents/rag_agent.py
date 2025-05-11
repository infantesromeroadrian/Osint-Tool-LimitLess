"""
RAG Agent implementation using LangGraph.
"""
from typing import Dict, List, Any, TypedDict, Optional, Annotated, Union, Literal
import os
from typing_extensions import TypedDict

from langchain.tools import Tool
from langgraph.graph import StateGraph, END
import operator

from src.agents.tools.vector_search_tool import VectorSearchTool
from src.agents.tools.document_processor_tool import DocumentProcessorTool
from src.agents.tools.response_generator_tool import ResponseGeneratorTool

# Define the agent state
class AgentState(TypedDict):
    """State for the RAG agent workflow."""
    query: str
    original_query: str
    retrieved_documents: List[Dict[str, Any]]
    analysis: Dict[str, Any]
    refined_query: Optional[str]
    response: Optional[Dict[str, Any]]
    chat_history: Optional[List[Dict[str, str]]]
    refinement_count: int
    temperature: float
    max_tokens: int
    top_k: int

class RAGAgent:
    """RAG Agent that uses LangGraph to orchestrate the RAG process."""
    
    def __init__(self):
        """Initialize the RAG agent with required tools."""
        self.vector_search = VectorSearchTool()
        self.document_processor = DocumentProcessorTool()
        self.response_generator = ResponseGeneratorTool()
        
        # Build the graph
        self.workflow = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow.
        
        Returns:
            Compiled StateGraph
        """
        # Create a new graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each step in the RAG process
        workflow.add_node("retrieve", self._retrieve_documents)
        workflow.add_node("analyze", self._analyze_documents)
        workflow.add_node("refine", self._refine_query)
        workflow.add_node("respond", self._generate_response)
        
        # Define the edges between nodes
        workflow.add_edge("retrieve", "analyze")
        
        # Conditional edge from analyze: either refine or respond
        workflow.add_conditional_edges(
            "analyze",
            self._should_refine_or_respond,
            {
                "refine": "refine",
                "respond": "respond"
            }
        )
        
        # From refine, go back to retrieve
        workflow.add_edge("refine", "retrieve")
        
        # Response is the end state
        workflow.add_edge("respond", END)
        
        # Set the entry point
        workflow.set_entry_point("retrieve")
        
        # Compile the graph
        return workflow.compile()
    
    def _retrieve_documents(self, state: AgentState) -> Dict[str, Any]:
        """Retrieve relevant documents for the query.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with retrieved documents
        """
        query = state["query"]
        top_k = state.get("top_k", 5)
        
        # Retrieve documents
        documents = self.vector_search.search(
            query=query,
            top_k=top_k
        )
        
        return {"retrieved_documents": documents}
    
    def _analyze_documents(self, state: AgentState) -> Dict[str, Any]:
        """Analyze retrieved documents for relevance.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with document analysis
        """
        query = state["query"]
        documents = state["retrieved_documents"]
        
        # Analyze documents
        analysis = self.document_processor.analyze_relevance(
            query=query,
            documents=documents
        )
        
        return {"analysis": analysis}
    
    def _should_refine_or_respond(self, state: AgentState) -> Literal["refine", "respond"]:
        """Determine whether to refine the query or respond.
        
        Args:
            state: Current agent state
            
        Returns:
            Next node to transition to
        """
        analysis = state["analysis"]
        refinement_count = state.get("refinement_count", 0)
        
        # If refinement is needed and we haven't refined too many times
        if analysis.get("needs_refinement", False) and refinement_count < 2:
            return "refine"
        
        # Otherwise, respond with what we have
        return "respond"
    
    def _refine_query(self, state: AgentState) -> Dict[str, Any]:
        """Refine the query based on analysis.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with refined query
        """
        original_query = state.get("original_query", state["query"])
        analysis = state["analysis"]
        documents = state["retrieved_documents"]
        refinement_count = state.get("refinement_count", 0)
        
        # Refine the query
        refined_query = self.document_processor.refine_query(
            original_query=original_query,
            analysis=analysis,
            retrieved_documents=documents
        )
        
        return {
            "query": refined_query,
            "refined_query": refined_query,
            "refinement_count": refinement_count + 1
        }
    
    def _generate_response(self, state: AgentState) -> Dict[str, Any]:
        """Generate the final response.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with generated response
        """
        query = state.get("original_query", state["query"])
        documents = state["retrieved_documents"]
        analysis = state["analysis"]
        chat_history = state.get("chat_history")
        temperature = state.get("temperature", 0.7)
        max_tokens = state.get("max_tokens", 500)
        
        # Check if we have documents
        if documents:
            # Generate answer with RAG
            response = self.response_generator.generate_answer(
                query=query,
                documents=documents,
                analysis=analysis,
                temperature=temperature,
                max_tokens=max_tokens,
                chat_history=chat_history
            )
        else:
            # Generate fallback response
            response = self.response_generator.generate_fallback_response(
                query=query,
                chat_history=chat_history
            )
        
        return {"response": response}
    
    def query(
        self, 
        query: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        top_k: int = 5,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Run the RAG agent to answer a query.
        
        Args:
            query: User's query
            temperature: Temperature for LLM
            max_tokens: Maximum tokens for response
            top_k: Number of documents to retrieve
            chat_history: Optional chat history
            
        Returns:
            Response from the agent
        """
        # Initialize state
        initial_state: AgentState = {
            "query": query,
            "original_query": query,
            "retrieved_documents": [],
            "analysis": {},
            "refined_query": None,
            "response": None,
            "chat_history": chat_history,
            "refinement_count": 0,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_k": top_k
        }
        
        # Execute the graph
        result = self.workflow.invoke(initial_state)
        
        # Return the final response
        return {
            "answer": result["response"]["answer"],
            "sources": [doc for doc in result["retrieved_documents"]],
            "query": query,
            "refined_query": result.get("refined_query"),
            "confidence": result["response"].get("confidence", "low")
        } 