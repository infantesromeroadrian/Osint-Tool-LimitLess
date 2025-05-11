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
        
        if st.button("Search Intelligence"):
            if query:
                with st.spinner("Analyzing intelligence data..."):
                    # Get search results
                    results = self.search_service.search(
                        query=query,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    # Display results
                    st.subheader("Intelligence Results")
                    st.markdown(results["answer"])
                    
                    # Display sources only if they exist
                    if results.get("sources") and len(results["sources"]) > 0:
                        st.subheader("Intelligence Sources")
                        for i, source in enumerate(results["sources"]):
                            with st.expander(f"Source {i+1}: {source['title']}"):
                                st.markdown(source["content"])
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
                        for i, source in enumerate(message["sources"]):
                            st.markdown(f"**Source {i+1}: {source['title']}**")
                            st.markdown(source["content"])
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
                    # Use search service to get RAG-based response
                    results = self.search_service.search(
                        query=user_input,
                        temperature=chat_temperature,
                        max_tokens=chat_max_tokens,
                        top_k=top_k,
                        chat_history=st.session_state.chat_messages[:-1]  # Exclude the most recent user message
                    )
                    
                    response = results["answer"]
                    st.markdown(response)
                    
                    # Show sources in an expander only if sources exist
                    if results.get("sources") and len(results["sources"]) > 0:
                        with st.expander("View Sources"):
                            for i, source in enumerate(results["sources"]):
                                st.markdown(f"**Source {i+1}: {source['title']}**")
                                st.markdown(source["content"])
                                st.caption(f"Document: {source['document']} | Relevance: {source['relevance']:.2f}")
                                st.divider()
            
            # Add assistant response to chat history with sources
            chat_message = {
                "role": "assistant", 
                "content": response
            }
            
            # Only add sources if they exist
            if results.get("sources") and len(results["sources"]) > 0:
                chat_message["sources"] = results["sources"]
                
            st.session_state.chat_messages.append(chat_message) 