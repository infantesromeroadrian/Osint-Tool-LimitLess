from abc import ABC, abstractmethod

class BaseController(ABC):
    """Abstract base controller defining common controller interface."""
    
    @abstractmethod
    def render(self):
        """Render the controller's view."""
        pass 