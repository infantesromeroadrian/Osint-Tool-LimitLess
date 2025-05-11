from abc import ABC, abstractmethod

class BaseService(ABC):
    """Base service class defining the common interface for services."""
    
    @abstractmethod
    def __init__(self):
        """Initialize the service with required dependencies."""
        pass 