import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

def init_chat_history():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            AIMessage(content="Hello! Ask me anything about your database."),
        ]

def add_message(role, content):
    """Add a message to chat history."""
    message = AIMessage(content=content) if role == "AI" else HumanMessage(content=content)
    st.session_state.chat_history.append(message)

def display_chat_history():
    """Display the chat history in Streamlit."""
    for message in st.session_state.chat_history:
        if isinstance(message, AIMessage):
            with st.chat_message("AI"):
                st.markdown(message.content)
        elif isinstance(message, HumanMessage):
            with st.chat_message("Human"):
                st.markdown(message.content)
