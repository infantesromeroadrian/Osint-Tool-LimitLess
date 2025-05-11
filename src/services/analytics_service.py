import pandas as pd
from services.services import BaseService
from models.document_model import DocumentModel

class AnalyticsService(BaseService):
    """Service for providing analytics data for the dashboard."""
    
    def __init__(self):
        """Initialize analytics service with required dependencies."""
        self.document_model = DocumentModel()
    
    def get_document_count(self):
        """Get the total number of processed documents."""
        # In production, this would query the database
        return self.document_model.count_documents()
    
    def get_query_count(self):
        """Get the total number of intelligence queries."""
        # In production, this would query the database
        return 127
    
    def get_insight_count(self):
        """Get the total number of insights generated."""
        # In production, this would be calculated from query results
        return 85
    
    def get_recent_activity(self):
        """Get recent activity data for the dashboard."""
        # This would be fetched from a database in production
        return [
            {"type": "Document Upload", "description": "Financial report.pdf processed", "time_ago": "2 minutes ago"},
            {"type": "Intelligence Query", "description": "Analysis of threat actors in reports", "time_ago": "15 minutes ago"},
            {"type": "New Insight", "description": "Connection identified between entities", "time_ago": "45 minutes ago"},
            {"type": "Document Upload", "description": "Threat intelligence report.txt processed", "time_ago": "1 hour ago"}
        ]
    
    def get_document_type_distribution(self):
        """Get distribution of document types for visualization."""
        # This would be calculated from actual data in production
        data = {
            "Document Type": ["PDF", "CSV", "TXT", "DOCX", "Other"],
            "Count": [14, 8, 10, 5, 3]
        }
        return pd.DataFrame(data).set_index("Document Type") 