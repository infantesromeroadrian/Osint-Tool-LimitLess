import os
import uuid
from typing import Dict, List, Any
from datetime import datetime

def generate_unique_id() -> str:
    """Generate a unique ID for documents and other entities.
    
    Returns:
        A unique string identifier
    """
    return str(uuid.uuid4())

def get_file_extension(filename: str) -> str:
    """Get the file extension from a filename.
    
    Args:
        filename: The name of the file
        
    Returns:
        The file extension without the dot
    """
    return filename.split(".")[-1].lower()

def format_timestamp(timestamp: datetime = None) -> str:
    """Format a timestamp for display.
    
    Args:
        timestamp: The timestamp to format, defaults to current time
        
    Returns:
        Formatted timestamp string
    """
    timestamp = timestamp or datetime.now()
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def ensure_directory_exists(directory_path: str) -> None:
    """Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size.
    
    Args:
        lst: The list to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of list chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = "_") -> Dict[str, Any]:
    """Flatten a nested dictionary.
    
    Args:
        d: The dictionary to flatten
        parent_key: The parent key for nested dictionaries
        sep: Separator between nested keys
        
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items) 