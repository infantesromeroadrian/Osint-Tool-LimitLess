import os
import shutil
import json
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CaseService")

class CaseService:
    """Service for managing OSINT investigation cases."""
    
    def __init__(self):
        """Initialize the case management service."""
        self.base_dir = Path(os.path.abspath("data/casos"))
        self.cases_index_file = self.base_dir / "cases_index.json"
        
        # Ensure cases directory exists
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Create cases index if it doesn't exist
        if not self.cases_index_file.exists():
            self._create_empty_index()
    
    def _create_empty_index(self):
        """Create an empty cases index file."""
        empty_index = {"cases": []}
        with open(self.cases_index_file, "w", encoding="utf-8") as f:
            json.dump(empty_index, f, indent=2)
    
    def _load_cases_index(self):
        """Load the cases index from the JSON file."""
        try:
            with open(self.cases_index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cases index: {str(e)}")
            return {"cases": []}
    
    def _save_cases_index(self, index_data):
        """Save the cases index to the JSON file."""
        try:
            with open(self.cases_index_file, "w", encoding="utf-8") as f:
                json.dump(index_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving cases index: {str(e)}")
            return False
    
    def create_case(self, case_name, description=""):
        """
        Create a new investigation case.
        
        Args:
            case_name: Name of the case
            description: Optional description of the case
            
        Returns:
            tuple: (success, case_id or error_message)
        """
        try:
            # Generate a unique case ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            case_id = f"{case_name.replace(' ', '_')}_{timestamp}"
            
            # Create case directory structure
            case_dir = self.base_dir / case_id
            
            # Create subdirectories for different data types
            os.makedirs(case_dir, exist_ok=True)
            os.makedirs(case_dir / "documents", exist_ok=True)
            os.makedirs(case_dir / "transcriptions", exist_ok=True)
            os.makedirs(case_dir / "image_analysis", exist_ok=True)
            os.makedirs(case_dir / "chroma_db", exist_ok=True)
            
            # Update cases index
            cases_index = self._load_cases_index()
            case_info = {
                "id": case_id,
                "name": case_name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat()
            }
            cases_index["cases"].append(case_info)
            
            self._save_cases_index(cases_index)
            
            # Create a case metadata file
            with open(case_dir / "case_metadata.json", "w", encoding="utf-8") as f:
                json.dump(case_info, f, indent=2)
            
            logger.info(f"Created new case: {case_id}")
            return True, case_id
            
        except Exception as e:
            logger.error(f"Error creating case: {str(e)}")
            return False, f"Error creating case: {str(e)}"
    
    def delete_case(self, case_id):
        """
        Delete an investigation case.
        
        Args:
            case_id: ID of the case to delete
            
        Returns:
            bool: Success or failure
        """
        try:
            case_dir = self.base_dir / case_id
            
            # Check if case exists
            if not case_dir.exists():
                logger.warning(f"Case directory not found: {case_id}")
                return False
            
            # Remove case directory and all contents
            shutil.rmtree(case_dir)
            
            # Update cases index
            cases_index = self._load_cases_index()
            cases_index["cases"] = [case for case in cases_index["cases"] if case["id"] != case_id]
            self._save_cases_index(cases_index)
            
            logger.info(f"Deleted case: {case_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting case: {str(e)}")
            return False
    
    def get_cases(self):
        """
        Get a list of all investigation cases.
        
        Returns:
            list: List of case information dictionaries
        """
        cases_index = self._load_cases_index()
        return cases_index["cases"]
    
    def get_case_info(self, case_id):
        """
        Get information about a specific case.
        
        Args:
            case_id: ID of the case
            
        Returns:
            dict: Case information or None if not found
        """
        cases = self.get_cases()
        for case in cases:
            if case["id"] == case_id:
                return case
        return None
    
    def set_active_case(self, case_id):
        """
        Set a case as the active investigation.
        
        Args:
            case_id: ID of the case to set as active
            
        Returns:
            bool: Success or failure
        """
        # Check if case exists
        case_info = self.get_case_info(case_id)
        if not case_info:
            logger.warning(f"Case not found: {case_id}")
            return False
        
        # Write the active case ID to a file
        try:
            with open(self.base_dir / "active_case.txt", "w", encoding="utf-8") as f:
                f.write(case_id)
            logger.info(f"Set active case: {case_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting active case: {str(e)}")
            return False
    
    def get_active_case(self):
        """
        Get the currently active investigation case.
        
        Returns:
            str: Active case ID or None if not set
        """
        active_case_file = self.base_dir / "active_case.txt"
        if not active_case_file.exists():
            return None
        
        try:
            with open(active_case_file, "r", encoding="utf-8") as f:
                case_id = f.read().strip()
            return case_id
        except Exception as e:
            logger.error(f"Error getting active case: {str(e)}")
            return None
    
    def clear_active_case(self):
        """
        Clear the currently active investigation case.
        
        Returns:
            bool: Success or failure
        """
        active_case_file = self.base_dir / "active_case.txt"
        if active_case_file.exists():
            try:
                os.remove(active_case_file)
                logger.info("Cleared active case")
                return True
            except Exception as e:
                logger.error(f"Error clearing active case: {str(e)}")
                return False
        return True  # No active case to clear 