import os
from pathlib import Path
from services.case_service import CaseService

class CasePathResolver:
    """Utility to resolve file paths based on the active case."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CasePathResolver, cls).__new__(cls)
            cls._instance._case_service = CaseService()
        return cls._instance
    
    def get_case_directory(self, subdir=None):
        """
        Get the directory path for the active case.
        
        Args:
            subdir: Optional subdirectory within the case folder
            
        Returns:
            Path: Path object for the case directory or subdirectory
        """
        # Get active case ID
        active_case_id = self._case_service.get_active_case()
        
        # If no active case, use default directories
        if not active_case_id:
            base_dir = Path(os.path.abspath(f"data/{subdir or ''}"))
            os.makedirs(base_dir, exist_ok=True)
            return base_dir
        
        # Use case-specific directory
        case_dir = Path(os.path.abspath(f"data/casos/{active_case_id}"))
        
        # If subdirectory specified, append it
        if subdir:
            case_dir = case_dir / subdir
            
        # Ensure directory exists
        os.makedirs(case_dir, exist_ok=True)
        
        return case_dir
    
    def resolve_path(self, base_path, file_path):
        """
        Resolve a file path based on active case.
        
        Args:
            base_path: Base directory type (documents, transcriptions, etc.)
            file_path: Relative file path within the base directory
            
        Returns:
            str: Full path to the file in the active case context
        """
        case_dir = self.get_case_directory(base_path)
        return str(case_dir / file_path)
    
    def get_active_case_info(self):
        """
        Get information about the active case.
        
        Returns:
            dict: Case information or None if no active case
        """
        active_case_id = self._case_service.get_active_case()
        if active_case_id:
            return self._case_service.get_case_info(active_case_id)
        return None 