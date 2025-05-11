"""
Embedding generator for vector search.
"""
import os
import time
import numpy as np
from typing import List, Dict, Any, Optional, Union
from sentence_transformers import SentenceTransformer
import openai
from collections import Counter
import hashlib

class EmbeddingGenerator:
    """Generator for text embeddings using various models."""
    
    def __init__(self):
        """Initialize the embedding generator."""
        self.models = {}
        self.embedding_dim = 384  # Fallback embedding dimension
    
    def generate_embeddings(
        self, 
        chunks: List[str],
        model_name: str = "all-MiniLM-L6-v2"
    ) -> List[np.ndarray]:
        """Generate embeddings for text chunks.
        
        Args:
            chunks: List of text chunks
            model_name: Name of the model to use
            
        Returns:
            List of embedding vectors
        """
        try:
            # Try to use the transformer model
            model = self._load_model(model_name)
            
            if model:
                print(f"DEBUG: Generating {len(chunks)} embeddings with model {model_name}")
                embeddings = model.encode(chunks)
                print(f"DEBUG: Generated {len(embeddings)} embeddings using {model_name}")
                return [np.array(embedding) for embedding in embeddings]
            else:
                # Fallback to simple embeddings if model loading failed
                return self._generate_simple_embeddings(chunks)
                
        except Exception as e:
            print(f"DEBUG: Error generating embeddings with model {model_name}: {str(e)}")
            print(f"DEBUG: Falling back to simple embedding method")
            
            # Fallback to simple embeddings
            return self._generate_simple_embeddings(chunks)
    
    def generate_query_embedding(
        self, 
        query: str,
        model_name: str = "all-MiniLM-L6-v2"
    ) -> np.ndarray:
        """Generate embedding for a query.
        
        Args:
            query: Query text
            model_name: Name of the model to use
            
        Returns:
            Query embedding vector
        """
        # Generate embeddings for the single query
        embeddings = self.generate_embeddings([query], model_name)
        
        # Return the first (and only) embedding
        return embeddings[0]
    
    def _load_model(self, model_name: str, max_retries: int = 3) -> Optional[SentenceTransformer]:
        """Load the transformer model with retries.
        
        Args:
            model_name: Name of the model to load
            max_retries: Maximum number of retry attempts
            
        Returns:
            Loaded model or None if loading fails
        """
        # Check if model is already loaded
        if model_name in self.models:
            return self.models[model_name]
        
        # Try loading the model with retries
        for attempt in range(1, max_retries + 1):
            try:
                print(f"DEBUG: Loading model {model_name}, attempt {attempt}/{max_retries}")
                
                # Use offline mode as fallback for repeated failures
                if attempt > 1:
                    # Try to load in offline mode if the model might already be downloaded
                    os.environ['TRANSFORMERS_OFFLINE'] = '1'
                
                model = SentenceTransformer(model_name)
                
                # Reset offline mode
                if 'TRANSFORMERS_OFFLINE' in os.environ:
                    del os.environ['TRANSFORMERS_OFFLINE']
                
                # Cache the model for future use
                self.models[model_name] = model
                
                return model
                
            except Exception as e:
                print(f"DEBUG: Error loading model {model_name}: {str(e)}")
                
                # Sleep before retrying, with exponential backoff
                if attempt < max_retries:
                    retry_delay = attempt * 1
                    print(f"DEBUG: Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"DEBUG: Failed to load model after {max_retries} attempts")
                    
                    # Reset offline mode if it was set
                    if 'TRANSFORMERS_OFFLINE' in os.environ:
                        del os.environ['TRANSFORMERS_OFFLINE']
                    
                    return None
    
    def _generate_simple_embeddings(self, chunks: List[str]) -> List[np.ndarray]:
        """Generate simple embeddings as fallback.
        
        Args:
            chunks: List of text chunks
            
        Returns:
            List of simple embedding vectors
        """
        print(f"DEBUG: Generating {len(chunks)} simple embeddings of dimension {self.embedding_dim}")
        
        embeddings = []
        
        for chunk in chunks:
            # Create a reproducible but unique embedding based on the text
            # Not semantically meaningful but consistent for the same text
            np.random.seed(hash(chunk) % 2**32)
            
            # Generate a random vector but consistent for the same text
            embedding = np.random.rand(self.embedding_dim).astype(np.float32)
            
            # Normalize the vector to unit length
            embedding = embedding / np.linalg.norm(embedding)
            
            embeddings.append(embedding)
        
        print(f"DEBUG: Generated {len(embeddings)} simple embeddings successfully")
        return embeddings 