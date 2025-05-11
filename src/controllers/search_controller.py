import streamlit as st
from controllers.controllers import BaseController
from services.search_service import SearchService

class SearchController(BaseController):
    """Controller for intelligence search and RAG capabilities."""
    
    def __init__(self):
        """Initialize search controller with required services."""
        self.search_service = SearchService()
        
        # Initialize session state for interface selection if it doesn't exist
        if "search_interface" not in st.session_state:
            st.session_state.search_interface = "standard"  # Default to standard search
            
        # Initialize session state for agent usage
        if "use_advanced_rag" not in st.session_state:
            st.session_state.use_advanced_rag = True  # Enable advanced RAG by default
            
        # Initialize session state for news agent usage
        if "use_news_agent" not in st.session_state:
            st.session_state.use_news_agent = True  # Enable news agent by default
    
    def render(self):
        """Render the intelligence search view."""
        st.title("🔎 Search Intelligence")
        
        # Radio buttons for interface selection (outside of any container)
        interface_option = st.radio(
            "Select Interface",
            ["Standard Search", "Chat Interface"],
            index=0 if st.session_state.search_interface == "standard" else 1,
            horizontal=True,
        )
        
        # Update session state based on selection
        st.session_state.search_interface = "standard" if interface_option == "Standard Search" else "chat"
        
        # Advanced options in expander
        with st.expander("Advanced Options"):
            # Add toggle for advanced RAG agent
            st.session_state.use_advanced_rag = st.toggle(
                "Use Advanced RAG Agent",
                value=st.session_state.use_advanced_rag,
                help="Enable to use the advanced RAG agent with query refinement capabilities"
            )
            
            # Add toggle for news agent
            st.session_state.use_news_agent = st.toggle(
                "Use News Agent",
                value=st.session_state.use_news_agent,
                help="Enable to incorporate recent news alongside your document knowledge base"
            )
            
            if st.session_state.use_advanced_rag:
                st.info("The advanced RAG agent will analyze document relevance and refine queries when needed to improve results.")
                
            if st.session_state.use_news_agent:
                st.info("The news agent will search for recent news articles related to your query and combine this information with document knowledge.")
        
        # Render the appropriate interface
        if st.session_state.search_interface == "standard":
            self.render_standard_search()
        else:
            self.render_chat_interface()
    
    def render_standard_search(self):
        """Render the standard intelligence search interface."""
        st.write("Query your intelligence database with natural language.")
        
        # Search input
        query = st.text_input("Enter your intelligence query", 
                             key="standard_query",
                             placeholder="e.g., What are the key threats mentioned in the documents?")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            temperature = st.slider("Response Temperature", 0.0, 1.0, 0.7, 0.1,
                                   help="Higher values make output more creative, lower values more deterministic")
        
        with col2:
            max_tokens = st.slider("Max Response Length", 100, 1000, 500, 50)
            
        # Add retrieved documents slider
        top_k = st.slider("Number of Documents to Retrieve", 3, 10, 5, 1,
                          help="Number of document chunks to retrieve for each query")
        
        # News-specific options if news agent is enabled
        days_back = 7  # Default value
        if st.session_state.use_news_agent:
            days_back = st.slider("Days of News History", 1, 30, 7, 1,
                               help="Number of days to look back for relevant news")
        
        if st.button("Search Intelligence"):
            if query:
                with st.spinner("Analyzing intelligence data..."):
                    # Get search results with agent flags
                    results = self.search_service.search(
                        query=query,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_k=top_k,
                        use_agent=st.session_state.use_advanced_rag,
                        use_news=st.session_state.use_news_agent
                    )
                    
                    # Display results
                    st.subheader("Intelligence Results")
                    st.markdown(results["answer"])
                    
                    # Show which source was primary if using multi-agent
                    if results.get("using_news") and results.get("primary_source"):
                        source_type = results.get("primary_source")
                        if source_type == "combined":
                            st.success("This answer combines information from both your documents and recent news.")
                        elif source_type == "documents":
                            st.info("This answer is primarily based on your document knowledge base.")
                        elif source_type == "news":
                            st.info("This answer is primarily based on recent news articles.")
                    
                    # Display sources only if they exist
                    if results.get("sources") and len(results["sources"]) > 0:
                        st.subheader("Intelligence Sources")
                        
                        # Group sources by type if using news agent
                        if results.get("using_news"):
                            # Separate document and news sources
                            doc_sources = [s for s in results["sources"] if s.get("source_type") == "Document"]
                            news_sources = [s for s in results["sources"] if s.get("source_type") == "News"]
                            
                            # Show document sources first if any
                            if doc_sources:
                                st.markdown("#### Document Sources")
                                for i, source in enumerate(doc_sources):
                                    with st.expander(f"Source {i+1}: {source['title']}"):
                                        st.markdown(source['content'])
                                        st.caption(f"Document: {source['document']} | Relevance: {source['relevance']:.2f}")
                            
                            # Then show news sources if any
                            if news_sources:
                                st.markdown("#### News Sources")
                                for i, source in enumerate(news_sources):
                                    with st.expander(f"News {i+1}: {source['title']}"):
                                        st.markdown(source['content'])
                                        news_source = source.get('document', 'Unknown Source')
                                        date = f" | Date: {source.get('published_at', 'Unknown')}" if source.get('published_at') else ""
                                        st.caption(f"Source: {news_source}{date}")
                                        if source.get('url'):
                                            st.markdown(f"[Read full article]({source['url']})")
                        else:
                            # Standard source display for RAG-only
                            for i, source in enumerate(results["sources"]):
                                with st.expander(f"Source {i+1}: {source['title']}"):
                                    st.markdown(source['content'])
                                    st.caption(f"Document: {source['document']} | Relevance: {source['relevance']:.2f}")
            else:
                st.warning("Please enter a query to search intelligence data.")
    
    def render_chat_interface(self):
        """Render the chat interface for conversational RAG."""
        st.write("Chat with your intelligence data through natural conversation.")
        
        # Configuration in sidebar when in chat mode
        with st.sidebar:
            st.subheader("Chat Configuration")
            chat_temperature = st.slider("Chat Temperature", 0.0, 1.0, 0.7, 0.1, 
                                        key="chat_temperature",
                                        help="Higher values make responses more creative, lower values more deterministic")
            chat_max_tokens = st.slider("Max Response Length", 100, 1000, 500, 50, 
                                       key="chat_max_tokens")
            top_k = st.slider("Number of Sources to Retrieve", 3, 10, 5, 1,
                             key="top_k_sources",
                             help="Number of document chunks to retrieve for each query")
            
            # News-specific options if news agent is enabled
            if st.session_state.use_news_agent:
                days_back = st.slider("Days of News History", 1, 30, 7, 1,
                                     key="news_days_back",
                                     help="Number of days to look back for relevant news")
            
            # Add clear chat button to sidebar
            if "chat_messages" in st.session_state and st.session_state.chat_messages and st.button("Clear Chat History"):
                st.session_state.chat_messages = []
                st.rerun()
        
        # Initialize chat history in session state if it doesn't exist
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        
        # Display chat messages
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # For assistant messages, add a source toggle if sources exist
                if message["role"] == "assistant" and "sources" in message and message["sources"]:
                    with st.expander("View Sources"):
                        # Group sources by type if using news agent
                        if any(s.get("source_type") for s in message["sources"]):
                            # Separate document and news sources
                            doc_sources = [s for s in message["sources"] if s.get("source_type") == "Document"]
                            news_sources = [s for s in message["sources"] if s.get("source_type") == "News"]
                            
                            # Show document sources first if any
                            if doc_sources:
                                st.markdown("#### Document Sources")
                                for i, source in enumerate(doc_sources):
                                    st.markdown(f"**Source {i+1}: {source['title']}**")
                                    st.markdown(source['content'])
                                    st.caption(f"Document: {source['document']} | Relevance: {source['relevance']:.2f}")
                                    st.divider()
                            
                            # Then show news sources if any
                            if news_sources:
                                st.markdown("#### News Sources")
                                for i, source in enumerate(news_sources):
                                    st.markdown(f"**News {i+1}: {source['title']}**")
                                    st.markdown(source['content'])
                                    news_source = source.get('document', 'Unknown Source')
                                    date = f" | Date: {source.get('published_at', 'Unknown')}" if source.get('published_at') else ""
                                    st.caption(f"Source: {news_source}{date}")
                                    if source.get('url'):
                                        st.markdown(f"[Read full article]({source['url']})")
                                    st.divider()
                        else:
                            # Standard source display for RAG-only
                            for i, source in enumerate(message["sources"]):
                                st.markdown(f"**Source {i+1}: {source['title']}**")
                                st.markdown(source['content'])
                                st.caption(f"Document: {source['document']} | Relevance: {source['relevance']:.2f}")
                                st.divider()
        
        # Chat input (not inside any container)
        user_input = st.chat_input("Ask a question about your intelligence data...")
        
        # Handle user input
        if user_input:
            # Add user message to chat history
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(user_input)
            
            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Use search service to get RAG-based response with agent flags
                    results = self.search_service.search(
                        query=user_input,
                        temperature=chat_temperature,
                        max_tokens=chat_max_tokens,
                        top_k=top_k,
                        chat_history=st.session_state.chat_messages[:-1],  # Exclude the most recent user message
                        use_agent=st.session_state.use_advanced_rag,
                        use_news=st.session_state.use_news_agent
                    )
                    
                    response = results["answer"]
                    st.markdown(response)
                    
                    # Show which source was primary if using multi-agent
                    if results.get("using_news") and results.get("primary_source"):
                        source_type = results.get("primary_source")
                        if source_type == "combined":
                            st.success("This answer combines information from both your documents and recent news.")
                        elif source_type == "documents":
                            st.info("This answer is primarily based on your document knowledge base.")
                        elif source_type == "news":
                            st.info("This answer is primarily based on recent news articles.")
                    
                    # Show sources in an expander only if sources exist
                    if results.get("sources") and len(results["sources"]) > 0:
                        with st.expander("View Sources"):
                            # Group sources by type if using news agent
                            if results.get("using_news"):
                                # Separate document and news sources
                                doc_sources = [s for s in results["sources"] if s.get("source_type") == "Document"]
                                news_sources = [s for s in results["sources"] if s.get("source_type") == "News"]
                                
                                # Show document sources first if any
                                if doc_sources:
                                    st.markdown("#### Document Sources")
                                    for i, source in enumerate(doc_sources):
                                        st.markdown(f"**Source {i+1}: {source['title']}**")
                                        st.markdown(source['content'])
                                        st.caption(f"Document: {source['document']} | Relevance: {source['relevance']:.2f}")
                                        st.divider()
                                
                                # Then show news sources if any
                                if news_sources:
                                    st.markdown("#### News Sources")
                                    for i, source in enumerate(news_sources):
                                        st.markdown(f"**News {i+1}: {source['title']}**")
                                        st.markdown(source['content'])
                                        news_source = source.get('document', 'Unknown Source')
                                        date = f" | Date: {source.get('published_at', 'Unknown')}" if source.get('published_at') else ""
                                        st.caption(f"Source: {news_source}{date}")
                                        if source.get('url'):
                                            st.markdown(f"[Read full article]({source['url']})")
                                        st.divider()
                            else:
                                # Standard source display for RAG-only
                                for i, source in enumerate(results["sources"]):
                                    st.markdown(f"**Source {i+1}: {source['title']}**")
                                    st.markdown(source['content'])
                                    st.caption(f"Document: {source['document']} | Relevance: {source['relevance']:.2f}")
                                    st.divider()
            
            # Add response to chat history with sources
            st.session_state.chat_messages.append({
                "role": "assistant", 
                "content": response,
                "sources": results.get("sources", [])
            }) 