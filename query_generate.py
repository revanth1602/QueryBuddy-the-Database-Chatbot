from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
import re
import json
from bson import json_util
# from typing import Tuple


# Loading environment variables
load_dotenv()

"""
Generates query using chatgroq api
"""

def get_sql_chain(db):
    """
    Generates a SQL query based on the user's question and database schema.
    """
    template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's MySQL database.
    Based on the table schema below, write a SQL query that would answer the user's question. Take the conversation history into account.
    
    <SCHEMA>{schema}</SCHEMA>
    
    Conversation History: {chat_history}
    
    Write only the SQL query and nothing else. Do not wrap the SQL query in any other text, not even backticks. Do not escape any characters (e.g., do not use backslashes).
    
    For example:
    Question: What are the sales of July?
    SQL Query: SELECT SUM(sales) FROM sales WHERE month = 'July';
    Question: What about this month?
    SQL Query: SELECT SUM(sales) FROM sales WHERE month = 'August';
    
    Your turn:
    
    Question: {question}
    SQL Query:
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    
    # Using Groq api 
    llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama-3.3-70b-versatile", temperature=0) 
    
    def get_schema(_):
        return db.get_table_info()
    
    return (
        RunnablePassthrough.assign(schema=get_schema)
        | prompt
        | llm
        | StrOutputParser()
    )


def get_mongodb_query_chain(db):
    """
    Generates a MongoDB query based on the user's question.
    """
    template = """
    You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's MongoDB database.
    Based on the database schema below, write a MongoDB query that would answer the user's question. Take the conversation history into account.
    
    <SCHEMA>{schema}</SCHEMA>
    
    Conversation History: {chat_history}
    
    Write only the MongoDB query and nothing else. Do not wrap the query in any other text, not even backticks.
    For example:
    Question: Find the top 3 artists with the most tracks.
    MongoDB Query: db.tracks.aggregate([{{ "$group": {{ "_id": "$artistId", "track_count": {{ "$sum": 1 }} }}, {{ "$sort": {{ "track_count": -1 }} }}, {{ "$limit": 3 }}])
    Question: Find 10 artists.
    MongoDB Query: db.artists.find({{}}.project({{ "name": 1 }}).limit(10))
    For the above query donot give the query as db.artists.find({{}}, {{ "name": 1 }}).limit(10).
    When asked about find queries:
    - Use the projection as the SECOND argument
    - Always use double quotes for keys
    - Never chain .project() separately
    Ensure all property names are enclosed in double quotes (e.g., {{ "name": "value"}}) to comply with strict JSON syntax, even though MongoDB allows unquoted keys.Ensure that the queries comply with ATLAS Mongodb JSON Syntax.
    
    
    Your turn:
    
    Question: {question}
    MongoDB Query:
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    # Use Groq or OpenAI LLM
    llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"),model="llama-3.3-70b-versatile", temperature=0) 
    
    def get_schema(_):
        """Generate schema information with sample documents"""
        schema_info = []
        for col in db.list_collection_names():
            docs = list(db[col].find().limit(3))
            if not docs:
                schema_info.append(f"Collection: {col} (empty)")
                continue
                
            samples = []
            for doc in docs:
                doc.pop('_id', None)
                samples.append(json.dumps(doc, default=json_util.default))
            
            schema_info.append(
                f"Collection: {col}\nSample Documents:\n" + "\n".join(samples)
            )
        return "\n\n".join(schema_info)
    return (
        RunnablePassthrough.assign(schema=get_schema)
        | prompt
        | llm
        | StrOutputParser()
    )


"""
Executes the query and returns:
- The generated query.
- A natural language response summarizing the data.
"""

def get_response(db_type: str,user_query: str, db, chat_history: list):
    if db_type.lower() in ["mysql", "postgresql"]:
        # Generating SQL query
        try:
            sql_chain = get_sql_chain(db)
            query = sql_chain.invoke({
                "question": user_query,
                "chat_history": chat_history,  # Passing chat history for context
            })

            # Removing unwanted backslashes
            query = query.replace("\\", "") 

            print("\nGenerated SQL Query:\n", query)  # Debugging output

            # Executing SQL query and fetch raw data
            try:
                raw_data = db.run(query)
                # format(raw_data=raw_data)
                print("\n Raw Data from DB:", raw_data)  # Debugging output
            except Exception as e:
                print("\nDatabase Error:", str(e))
                return query, f"Database Error: {str(e)}"
            
            # Template for tabular output
            template = """
            You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
            Based on the table schema below, the SQL query, and the query results, format the data into a markdown table.
            
            <SCHEMA>{schema}</SCHEMA>
            
            SQL Query: <SQL>{query}</SQL>
            
            Query Results: {response}
            
            User Question: {question}

            
            Format the query results into a Markdown table with appropriate column names. Use the following format:
            
            ```
            | Column 1 | Column 2 | Column 3 | ... |
            |----------|----------|----------|-----|
            | Value 1  | Value 2  | Value 3  | ... |
            | Value 4  | Value 5  | Value 6  | ... |
            ```
            """

            prompt = ChatPromptTemplate.from_template(template)
            llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama-3.3-70b-versatile", temperature=0)
            
            chain = (
                RunnablePassthrough.assign(
                    schema=lambda _: db.get_table_info(),
                    response=lambda _: raw_data,  # Passing the raw data to the template
                )
                | prompt
                | llm
                | StrOutputParser()
            )

            # Generating the tabular output
            tabular_response = chain.invoke({
                "question": user_query,
                "query": query,
            })

            print("\nTabular Response:\n", tabular_response)  # Debugging output

            template = """
            You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's database.
            Based on the table schema below, the SQL query, and the query results, write a natural language response summarizing the data.
            Generate a human-readable response with proper spacing and punctuation.
            
            <SCHEMA>{schema}</SCHEMA>
            
            SQL Query: <SQL>{query}</SQL>
            
            Query Results: {response}
            
            User Question: {question}
            
            Write a response that summarizes the data in a clear and concise manner. Include key insights, trends, or anomalies if applicable.
            """
            
            prompt = ChatPromptTemplate.from_template(template)
            llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama-3.3-70b-versatile", temperature=0)
            
            chain = (
                RunnablePassthrough.assign(
                    schema=lambda _: db.get_table_info(),
                    response=lambda _: raw_data,  # Passing the raw data to the template
                )
                | prompt
                | llm
                | StrOutputParser()
            )

            # Generating the natural language response
            nl_response = chain.invoke({
                "question": user_query,
                "query": query,
            })
            print("\nNatural Language Response:\n", nl_response)  # Debugging output
            
            return query, nl_response,tabular_response
        except Exception as e:
                return query, f"Error executing query: {str(e)}", ""
        
    elif db_type.lower() == "mongodb":
            # Generating MongoDB query
            mongodb_chain = get_mongodb_query_chain(db)
            query = mongodb_chain.invoke({
                "question": user_query,
                "chat_history": chat_history,  # Passing chat history for context
            })
            
            print("\nGenerated MongoDB Query:\n", query)
            try:
                # Extracting collection name from query
                collection_name = re.search(r'db\.(\w+)\.', query).group(1)
                collection = db[collection_name]

                # Handle find() queries
                if '.find(' in query:
                    match = re.search(r'find\(\s*({.*?})\s*,\s*({.*?})\s*\)', query, re.DOTALL)
                    
                    filter_part = match.group(1).strip()
                    projection_part = match.group(2).strip() if match.group(2) else "{}"
                    filter_obj = json.loads(filter_part)
                    projection_obj = json.loads(projection_part)
                    raw_data = list(collection.find(filter_obj, projection_obj))
                # Handle aggregate() queries
                elif '.aggregate(' in query:
                    pipeline_part = re.search(r'aggregate\((\[.*?\])', query, re.DOTALL).group(1)
                    pipeline = json.loads(pipeline_part)
                    raw_data = list(collection.aggregate(pipeline))

                # Handle limit/sort modifiers
                if '.limit(' in query:
                    limit = int(re.search(r'limit\((\d+)\)', query).group(1))
                    raw_data = raw_data[:limit]

                print("\nRaw Data from MongoDB:\n", raw_data)

                # Converting raw data to JSON string for processing
                raw_data_str = json.dumps(raw_data, default=json_util.default)

                # Template for tabular output
                template = """
                You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's MongoDB database.
                Based on the query results below, format the data into a markdown table.
                
                MongoDB Query: <QUERY>{query}</QUERY>
                
                Query Results: {response}
                
                User Question: {question}

                Format the query results into a Markdown table with appropriate column names. If the data is nested, flatten it for display.Donot include column named id.
                Use the following format:
                
                ```
                | Column 1 | Column 2 | Column 3 | ... |
                |----------|----------|----------|-----|
                | Value 1  | Value 2  | Value 3  | ... |
                | Value 4  | Value 5  | Value 6  | ... |
                ```
                """

                prompt = ChatPromptTemplate.from_template(template)
                llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama-3.3-70b-versatile", temperature=0)
                
                chain = (
                    RunnablePassthrough.assign(
                        response=lambda _: raw_data_str,
                    )
                    | prompt
                    | llm
                    | StrOutputParser()
                )

                # Generating the tabular output
                tabular_response = chain.invoke({
                    "question": user_query,
                    "query": query,
                })

                print("\nTabular Response:\n", tabular_response)

                # Template for natural language response
                template = """
                You are a data analyst at a company. You are interacting with a user who is asking you questions about the company's MongoDB database.
                Based on the MongoDB query and the query results, write a natural language response summarizing the data.
                Generate a human-readable response with proper spacing and punctuation.
                MongoDB Query: <QUERY>{query}</QUERY>
                
                Query Results: {response}
                
                User Question: {question}
                
                Write a response that summarizes the data in a clear and concise manner. Include key insights, trends, or anomalies if applicable.
                Handle nested documents appropriately in your summary.
                """
                
                prompt = ChatPromptTemplate.from_template(template)
                llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama-3.3-70b-versatile", temperature=0)
                
                chain = (
                    RunnablePassthrough.assign(
                        response=lambda _: raw_data_str,
                    )
                    | prompt
                    | llm
                    | StrOutputParser()
                )

                # Generating the natural language response
                nl_response = chain.invoke({
                    "question": user_query,
                    "query": query,
                })

                print("\nNatural Language Response:\n", nl_response)
                
                return query, nl_response, tabular_response

            except Exception as e:
                return query, f"Error executing query: {str(e)}", ""