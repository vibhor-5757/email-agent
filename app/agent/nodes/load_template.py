from dotenv import load_dotenv
import psycopg2
from agent.nodes.shared import AgentState
from agent.sql_agent import agent_executor
import ast
import os

def connect_to_postgres():
    try:
        connection = psycopg2.connect(POSTGRES_URI)
        print("Connected to Supabase.")
        return connection
    except Exception as e:
        print("Connection failed:", e)
        return None
    
load_dotenv()
POSTGRES_URI = os.getenv("POSTGRES_URI")
connection = connect_to_postgres()
cursor = connection.cursor()

def load_template_by_name(state: AgentState) -> AgentState:
    
    print("entered load template")
    name = state["matched_template_name"]
    
    try:
        cursor.execute("SELECT subject, content FROM email_templates WHERE name = %s;", (name,))
        result = cursor.fetchone()  # fetch one row instead of fetchall
        if result:
            subject, content = result
            template = {"subject": subject, "content": content}
        else:
            template = {"subject": "", "content": ""}
        print("template==: ", template)
    except Exception as e:
        print("Error loading template:", e)
        template = {"subject": "", "content": ""}
    
    return {**state, "template": template}
