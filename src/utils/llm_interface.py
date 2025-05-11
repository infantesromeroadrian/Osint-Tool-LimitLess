import os
import sys
from typing import Dict, List, Any, Optional
import openai
from openai import OpenAI

class LLMInterface:
    """Interface for interacting with language models."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the LLM interface.
        
        Args:
            api_key: OpenAI API key (defaults to environment variable)
        """
        # Get the API key
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        # Create client instance for OpenAI v1.x
        self.client = OpenAI(api_key=api_key)
        
        # Print debug information
        print(f"OpenAI version: {openai.__version__}")
    
    def generate_answer(
        self, 
        query: str,
        context: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        model: str = "gpt-4-0125-preview"  # GPT-4.1 (latest version)
    ) -> str:
        """Generate an answer using the LLM.
        
        Args:
            query: User's query
            context: Context from retrieved documents
            temperature: Temperature for generation
            max_tokens: Maximum tokens in response
            model: Model to use
            
        Returns:
            Generated answer text
        """
        prompt = self._create_prompt(query, context)
        
        try:
            # Create API call using new style
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            # In production, this would be properly logged
            return f"Error generating response: {str(e)}"
    
    def generate_chat_response(
        self,
        query: str,
        context: str,
        chat_history: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        model: str = "gpt-4-0125-preview"  # GPT-4.1 (latest version)
    ) -> str:
        """Generate a response in a conversational context using RAG.
        
        Args:
            query: Current user query
            context: Context from retrieved documents
            chat_history: List of previous messages in the conversation
            temperature: Temperature for generation
            max_tokens: Maximum tokens in response
            model: Model to use
            
        Returns:
            Generated answer text
        """
        # Create message list starting with system prompt
        messages = [{"role": "system", "content": self._get_chat_system_prompt()}]
        
        # Add context message
        messages.append({
            "role": "system",
            "content": f"Here is relevant information from the intelligence database to help answer the user's questions:\n\n{context}"
        })
        
        # Add chat history (but limit to last 10 messages to prevent token overflow)
        for message in chat_history[-10:]:
            messages.append({"role": message["role"], "content": message["content"]})
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                frequency_penalty=0.3,
                presence_penalty=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            # In production, this would be properly logged
            return f"Error generating chat response: {str(e)}"
    
    def generate_general_response(
        self,
        query: str,
        chat_history: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
        model: str = "gpt-4-0125-preview"  # GPT-4.1 (latest version)
    ) -> str:
        """Generate a response using the LLM's general knowledge without document context.
        
        Args:
            query: Current user query
            chat_history: List of previous messages in the conversation
            temperature: Temperature for generation
            max_tokens: Maximum tokens in response
            model: Model to use
            
        Returns:
            Generated answer text
        """
        # Create message list starting with system prompt
        messages = [{"role": "system", "content": self._get_general_system_prompt()}]
        
        # Add chat history (but limit to last 10 messages to prevent token overflow)
        for message in chat_history[-10:]:
            messages.append({"role": message["role"], "content": message["content"]})
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                frequency_penalty=0.3,
                presence_penalty=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            # Log the error for debugging
            print(f"Error in generate_general_response: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def _create_prompt(self, query: str, context: str) -> str:
        """Create a RAG prompt combining query and context.
        
        Args:
            query: User's query
            context: Context from retrieved documents
            
        Returns:
            Formatted prompt
        """
        return f"""
Answer the following question based on the provided context from intelligence documents.

Context:
{context}

Question:
{query}

Provide a detailed and informative answer based only on the context provided. If the context doesn't contain enough information to answer the question fully, acknowledge the limitations of the available information.
"""
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for OSINT analysis.
        
        Returns:
            System prompt text
        """
        return """
You are an advanced OSINT (Open Source Intelligence) analysis assistant. Your role is to analyze information from various sources and provide objective, factual insights based on the provided context.

Guidelines:
1. Base your answers solely on the provided context
2. Maintain objectivity and avoid speculation
3. Present information clearly and concisely
4. Highlight connections between entities and events when relevant
5. Acknowledge limitations in the data when appropriate
6. Organize information logically for easy comprehension
7. Do not reveal sensitive or confidential information
8. Cite specific documents from the context when possible

Your analysis should help intelligence professionals make informed decisions based on the available information.
"""
    
    def _get_chat_system_prompt(self) -> str:
        """Get the system prompt for conversational OSINT analysis.
        
        Returns:
            System prompt text for chat mode
        """
        return """
You are an advanced OSINT (Open Source Intelligence) analysis assistant in conversation mode. Your role is to engage in a helpful dialogue with the user, analyzing information from various sources and providing objective, factual insights based on the provided context.

Guidelines:
1. Base your answers solely on the provided context
2. Maintain objectivity and avoid speculation
3. Present information clearly and concisely
4. Highlight connections between entities and events when relevant 
5. Acknowledge limitations in the data when appropriate
6. Respond in a conversational but professional tone
7. Remember previous messages in the conversation for context
8. Do not reveal sensitive or confidential information
9. Cite specific documents from the context when possible

Your goal is to help the user explore and understand the intelligence data through natural conversation.
"""
    
    def _get_general_system_prompt(self) -> str:
        """Get the system prompt for general AI conversation without document context.
        
        Returns:
            System prompt text for general conversation
        """
        return """
You are an advanced AI assistant with expertise in cybersecurity, intelligence analysis, and OSINT (Open Source Intelligence) techniques. Your role is to engage in a helpful dialogue with the user, answering questions to the best of your ability based on your general knowledge.

Guidelines:
1. Provide helpful, accurate, and informative responses
2. Be honest about limitations of your knowledge when appropriate
3. Present information clearly and in a conversational but professional tone
4. Emphasize cybersecurity best practices and ethical considerations
""" 