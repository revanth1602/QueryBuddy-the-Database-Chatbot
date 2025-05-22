from langchain_community.utilities.sql_database import SQLDatabase
from pymongo import MongoClient
from urllib.parse import quote_plus
import streamlit as st

def init_database(user, password, host, port, database, db_type):
    password = quote_plus(password)  # URL-encode the password
    db_type = db_type.lower()

    try:
        if db_type == "mysql":
            db_uri = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
            return SQLDatabase.from_uri(db_uri)

        elif db_type == "postgresql":
            db_uri = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
            return SQLDatabase.from_uri(db_uri)

        elif db_type == "mongodb":
            uri = f"mongodb+srv://{user}:{password}@{host}/{database}"
            client = MongoClient(
                uri,
                connectTimeoutMS=10000,
                serverSelectionTimeoutMS=5000,
                tlsAllowInvalidCertificates=False
            )
            return client[database]
            # client = MongoClient(f"mongodb://{user}:{password}@{host}:{port}")
            # db = client[database]
            # return db  # MongoDB client object

        else:
            st.error("Unsupported database type")
            return None

    except Exception as e:
        st.error(f"Error connecting to {db_type}: {e}")
        return None
