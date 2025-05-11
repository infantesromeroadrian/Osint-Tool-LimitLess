from typing import List, Dict, Any, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import openai
import time
import os
from collections import Counter
import hashlib

class EmbeddingGenerator:
    """Generator for text embeddings using various models."""
    
    def __init__(self):
        """Initialize the embedding generator."""
        self.models = {}
        self.fallback_mode = False
    
    def generate_embeddings(
        self, 
        texts: List[str], 
        model_name: str = "all-MiniLM-L6-v2"
    ) -> List[np.ndarray]:
        """Generate embeddings for a list of text chunks.
        
        Args:
            texts: List of text chunks to embed
            model_name: Name of the embedding model to use
            
        Returns:
            List of embedding vectors
        """
        # First try using specified model
        try:
            if model_name == "text-embedding-ada-002":
                return self._generate_openai_embeddings(texts)
            else:
                return self._generate_sentence_transformer_embeddings(texts, model_name)
        except Exception as e:
            print(f"DEBUG: Error generating embeddings with model {model_name}: {str(e)}")
            print("DEBUG: Falling back to simple embedding method")
            self.fallback_mode = True
            return self._generate_simple_embeddings(texts)
    
    def generate_query_embedding(
        self, 
        query: str, 
        model_name: str = "all-MiniLM-L6-v2"
    ) -> np.ndarray:
        """Generate embedding for a single query text.
        
        Args:
            query: Query text to embed
            model_name: Name of the embedding model to use
            
        Returns:
            Embedding vector for the query
        """
        embeddings = self.generate_embeddings([query], model_name)
        return embeddings[0]
    
    def _get_model(self, model_name: str) -> SentenceTransformer:
        """Get or load a SentenceTransformer model.
        
        Args:
            model_name: Name of the model to load
            
        Returns:
            Loaded model instance
        """
        if model_name not in self.models:
            # Try loading with retry mechanism
            max_retries = 3
            for i in range(max_retries):
                try:
                    print(f"DEBUG: Loading model {model_name}, attempt {i+1}/{max_retries}")
                    self.models[model_name] = SentenceTransformer(model_name)
                    print(f"DEBUG: Successfully loaded model {model_name}")
                    break
                except Exception as e:
                    print(f"DEBUG: Error loading model {model_name}: {str(e)}")
                    if i < max_retries - 1:
                        backoff_time = 2 ** i
                        print(f"DEBUG: Retrying in {backoff_time} seconds...")
                        time.sleep(backoff_time)
                    else:
                        print(f"DEBUG: Failed to load model after {max_retries} attempts")
                        raise
        return self.models[model_name]
    
    def _generate_sentence_transformer_embeddings(
        self, 
        texts: List[str],
        model_name: str
    ) -> List[np.ndarray]:
        """Generate embeddings using SentenceTransformers.
        
        Args:
            texts: List of text chunks to embed
            model_name: Name of the model to use
            
        Returns:
            List of embedding vectors
        """
        model = self._get_model(model_name)
        embeddings = model.encode(texts, show_progress_bar=False)
        return embeddings
    
    def _generate_openai_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using OpenAI API.
        
        Args:
            texts: List of text chunks to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        # Process in batches to respect API limits
        batch_size = 20
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            response = openai.embeddings.create(
                model="text-embedding-ada-002",
                input=batch
            )
            
            batch_embeddings = [np.array(item.embedding) for item in response.data]
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    def _generate_simple_embeddings(self, texts: List[str], dim: int = 384) -> List[np.ndarray]:
        """Generate simple embeddings without external models.
        
        This is a fallback method that creates embeddings based on word frequency and
        hashing when the primary methods fail. Not as effective but works offline.
        
        Args:
            texts: List of text chunks to embed
            dim: Dimensionality of embeddings (to match expected dimensions)
            
        Returns:
            List of embedding vectors
        """
        print(f"DEBUG: Generating {len(texts)} simple embeddings of dimension {dim}")
        embeddings = []
        
        for text in texts:
            # Create word frequency vector
            words = text.lower().split()
            counter = Counter(words)
            
            # Hash-based embedding for stability across runs
            embedding = np.zeros(dim, dtype=np.float32)
            
            for word, count in counter.items():
                # Generate a stable hash for each word
                word_hash = int(hashlib.md5(word.encode()).hexdigest(), 16)
                
                # Use the hash to determine positions in the embedding
                positions = [word_hash % dim]
                # Add a few more positions for more signal
                for i in range(5):
                    positions.append((word_hash + i*100) % dim)
                
                # Set those positions based on word frequency
                for pos in positions:
                    embedding[pos] += count
            
            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
                
            embeddings.append(embedding)
            
        print(f"DEBUG: Generated {len(embeddings)} simple embeddings successfully")
        return embeddings 