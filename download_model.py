import time
import os
from sentence_transformers import SentenceTransformer

def download_model(model_name="all-MiniLM-L6-v2", max_retries=5):
    """Download sentence transformer model with retries"""
    print(f"Attempting to download model: {model_name}")
    
    for i in range(max_retries):
        try:
            print(f"Attempt {i+1}/{max_retries}...")
            model = SentenceTransformer(model_name)
            print(f"Model {model_name} downloaded successfully!")
            return model
        except Exception as e:
            print(f"Error downloading model: {e}")
            if i < max_retries - 1:
                backoff_time = 2 ** i
                print(f"Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)
            else:
                print(f"Failed to download model after {max_retries} attempts")

if __name__ == "__main__":
    download_model() 