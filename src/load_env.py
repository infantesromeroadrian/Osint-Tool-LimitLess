import os
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env file."""
    # Load from .env file
    load_dotenv()
    
    # Check if the OpenAI API key is available
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("WARNING: OPENAI_API_KEY not found in environment variables or .env file.")
        print("Please set your OpenAI API key in the .env file or as an environment variable.")
    
    return api_key is not None 