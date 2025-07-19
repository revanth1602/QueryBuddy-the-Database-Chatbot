
import streamlit as st
from db_connector import init_database
from chat_history import init_chat_history, add_message, display_chat_history
from query_generate import get_response
from Format_query import format_query   
import time
from nl_format import format_nl_response

# Set page configuration
st.set_page_config(page_title="QueryBuddy", page_icon=":speech_balloon:")
init_chat_history()

# Custom CSS to hide the sidebar navigation

st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True
)

# Setting up session state for theme
ms = st.session_state
if "themes" not in ms: 
    ms.themes = {
        "current_theme": "light",
        "refreshed": True,
        "light": {
            "theme.base": "light",  # White background
            "theme.backgroundColor": "white",
            "theme.primaryColor": "#f1f1f1",  # Green primary color
            "theme.secondaryBackgroundColor": "#f1f1f9",
            "theme.textColor": "black",  # Black text
            "button_face": "🌞"
        },
        "dark": {
            "theme.base": "dark",  # Black background
            "theme.backgroundColor": "black",
            "theme.primaryColor": "#333338",  # Green primary color
            "theme.secondaryBackgroundColor": "#333333",
            "theme.textColor": "white",  # White text
            "button_face": "🌜"  
        },
    }

def ChangeTheme():
    previous_theme = ms.themes["current_theme"]
    tdict = ms.themes["light"] if ms.themes["current_theme"] == "light" else ms.themes["dark"]
    for vkey, vval in tdict.items(): 
        if vkey.startswith("theme"):
            st._config.set_option(vkey, vval)

    ms.themes["refreshed"] = False
    if previous_theme == "dark": 
        ms.themes["current_theme"] = "light"
    elif previous_theme == "light": 
        ms.themes["current_theme"] = "dark"

# Setting page title and centering it
st.markdown("<h1 style='text-align: center;'>QueryBuddy</h1>", unsafe_allow_html=True)

# Database options
options = ['MySQL', 'MongoDB', 'PostgreSQL']

# Sidebar for database connection
with st.sidebar:
    # Adding theme toggle button
    btn_face = ms.themes["light"]["button_face"] if ms.themes["current_theme"] == "light" else ms.themes["dark"]["button_face"]
    st.button(btn_face, on_click=ChangeTheme)
    db_type = st.selectbox("Select Database Type", options)
    st.text_input("Host", key="Host")
    st.text_input("Port", key="Port")
    st.text_input("User", key="User")
    st.text_input("Password", type="password", key="Password")
    st.text_input("Database", key="Database")

    # Custom CSS for button styling
    st.markdown("""
        <style>
            .stButton > button {
                background-color: #28a745;
                color: white;
                border-radius: 5px;
                padding: 0.5em 1em;
                font-size: 16px;
                border: none;
                transition: background-color 0.3s;
            }
            .stButton > button:hover {
                background-color: #5cd65c;
                color: white;
            }
            [data-testid="stSidebar"] {
                padding-top: 0 !important;
            }
            .st-emotion-cache-16txtl3 {
                padding: 3.9rem 1.5rem;
            }
        </style>
    """, unsafe_allow_html=True)

    # Connecting button
    if st.button("Connect"):
        with st.spinner("Connecting to Database..."):
            db = init_database(
                st.session_state["User"],
                st.session_state['Password'],
                st.session_state['Host'],
                st.session_state['Port'],
                st.session_state['Database'],
                db_type
            )
            if db is not None:
                st.session_state.db = db
                st.session_state.db_type = db_type  # Storing the database type
                st.success("Connected to database!")
            else:
                st.error("Failed to connect to the database. Please check your credentials.")

# Applying theme changes
if ms.themes["refreshed"] == False:
    ms.themes["refreshed"] = True
    st.rerun()

# Display chat history
display_chat_history()

# Chat input for user query
user_query = st.chat_input("Type a message...")

if user_query:
    # Adding user query to chat history
    add_message("Human", user_query)
    with st.chat_message("Human"):
        st.markdown(user_query)

    with st.chat_message("AI"):
        if "db" in st.session_state:
            with st.spinner("Generating response..."):
                # Passing the chat history to get_response
                query,nl_response,tabular_response = get_response(
                    st.session_state.db_type,
                    user_query,
                    st.session_state.db,
                    st.session_state.chat_history  # Pass chat history for context
                )

            if db_type in ['mysql','postgresql']:
                formatted_query = format_query(query)
                st.markdown("**Generated Query:**")
                st.code(formatted_query, language='sql')
                st.markdown("**Response:**")
                formatted_nl = format_nl_response(nl_response)
                response_placeholder = st.empty()
                full_response = ""
                for char in nl_response:
                    full_response += char
                    response_placeholder.markdown(full_response+ "▌")
                    time.sleep(0.01)
                response_placeholder.markdown(full_response)
                time.sleep(0.01)
                #st.write(nl_response)
                st.write(tabular_response)
            else:
                st.markdown("**Generated Query:**")
                st.code(query, language='javascript')
                st.markdown("**Response:**")
                formatted_nl = format_nl_response(nl_response)
                response_placeholder = st.empty()
                full_response = ""
                for char in nl_response:
                    full_response += char
                    response_placeholder.markdown(full_response+ "▌")
                    time.sleep(0.01)
                response_placeholder.markdown(full_response)
                time.sleep(0.01)
                #st.write(nl_response)
                st.write(tabular_response)

        else:
            st.error("Please connect to a database first.")

    # Add AI response to chat history
    add_message("AI", f"Query:\n```sql\n{query}\n```\n\nResponse:\n{formatted_nl} \n \n{tabular_response}")
