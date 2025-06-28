from agent.nodes.shared import AgentState
from agent.sql_agent import agent_executor

import psycopg2
import os
from dotenv import load_dotenv
import datetime

load_dotenv()
POSTGRES_URI = os.getenv("POSTGRES_URI")

def connect_to_postgres():
    try:
        connection = psycopg2.connect(POSTGRES_URI)
        return connection
    except Exception as e:
        print("Connection failed:", e)
        return None

def store_template(state: AgentState) -> AgentState:
    name = state.get("matched_template_name")
    
    if not name:
        
        try:
            name = input("Enter a name to save this template: ").strip()
        except:
            name = f"template_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        state["matched_template_name"] = name
    
    connection = connect_to_postgres()
    if not connection:
        print("Failed to connect to database")
        return state
    
    cursor = connection.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO email_templates (name, subject, content)
            VALUES (%s, %s, %s)
            ON CONFLICT(name) DO UPDATE SET
            subject = EXCLUDED.subject,
            content = EXCLUDED.content;
        """, (name, state['template']['subject'], state['template']['content']))
        
        connection.commit()
        print(f"✅ Template '{name}' saved successfully!")
        
    except Exception as e:
        print(f"❌ Error saving template: {e}")
    
    cursor.close()
    connection.close()
    
    return state

