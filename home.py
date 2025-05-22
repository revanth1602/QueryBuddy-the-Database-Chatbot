import streamlit as st

# Setting page config
st.set_page_config(page_title="QueryBuddy", page_icon=":speech_balloon:")

#Remove sidebar
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {display: none !important;}  /* Hides the sidebar completely */
        [data-testid="stToolbar"] {display: none !important;}  /* Hides the top toolbar */
    </style>
    """,
    unsafe_allow_html=True
)

# Custom CSS for styling
st.markdown("""
    <style>
        .centered-text {
            text-align: center;
            font-size: 28px;
            font-weight: bold;
        }
        .stButton > button {
            display: block;
            margin: 20px auto;
            background-color: #28a745;
            color: white;
            font-size: 18px;
            padding: 12px 24px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
        }
        .stButton > button:hover {
            background-color: #5cd65c;
        }
    </style>
""", unsafe_allow_html=True)

# Page Title
st.markdown("<h1 class='centered-text'>Welcome to QueryBuddy</h1>", unsafe_allow_html=True)

st.markdown("""
### What is QueryBuddy?
- 🚀 **AI-powered chatbot** that lets you interact with databases using natural language.
- 💾 Supports **MySQL, PostgreSQL, and MongoDB**.
- 🧠 Converts **human language into SQL queries** and retrieves data in a tabular format.
""")

if st.button("Enter Chatbot"):
    st.switch_page("pages/app.py") 
