import streamlit as st
from controllers.controllers import BaseController
from services.analytics_service import AnalyticsService

class DashboardController(BaseController):
    """Controller for the dashboard view."""
    
    def __init__(self):
        """Initialize dashboard controller with required services."""
        self.analytics_service = AnalyticsService()
    
    def render(self):
        """Render the dashboard view."""
        st.title("🔍 Limitless OSINT Dashboard")
        st.subheader("Open Source Intelligence Tool")
        
        # Dashboard layout with metrics and visualizations
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="Documents Processed", 
                     value=self.analytics_service.get_document_count(),
                     delta="↑2 today")
            
        with col2:
            st.metric(label="Intelligence Queries", 
                     value=self.analytics_service.get_query_count(),
                     delta="↑5 today")
            
        with col3:
            st.metric(label="Insights Generated", 
                     value=self.analytics_service.get_insight_count(),
                     delta="↑3 today")
        
        # Recent activity
        st.subheader("Recent Activity")
        recent_activity = self.analytics_service.get_recent_activity()
        for activity in recent_activity:
            st.info(f"**{activity['type']}**: {activity['description']} - {activity['time_ago']}")
        
        # Intelligence summary
        st.subheader("Intelligence Summary")
        st.write("Overview of key intelligence insights from your data.")
        
        # Placeholder for visualization
        st.bar_chart(self.analytics_service.get_document_type_distribution()) 