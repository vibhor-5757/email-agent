from langchain_google_genai import ChatGoogleGenerativeAI
import psycopg2
from agent.nodes.shared import AgentState
import os
from dotenv import load_dotenv

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

gemini_api_key2 = os.getenv("GEMINI_API_KEY2")
print(gemini_api_key2)

llm = ChatGoogleGenerativeAI(  
    model="gemini-1.5-flash",
    temperature=0,
    google_api_key=gemini_api_key2
)  

def match_existing_template(state: AgentState) -> AgentState:  
    try:
        cursor.execute("SELECT name, subject, content FROM email_templates;")
        rows = cursor.fetchall()
        templates = [{"name": row[0], "subject": row[1], "content": row[2]} for row in rows]
    except Exception as e:
        print("Error fetching templates:", e)
        templates = []

    matching_prompt = f"""
    User Intent: "{state['query_intent']}"
    Templates: {templates}
    
    Based on the user intent, determine if any existing template matches.
    If a template matches, respond with "MATCH: template_name"
    If no template matches, respond with "NO_MATCH"
    """

    response = llm.invoke(matching_prompt)
    decision = response.content.strip()

    if decision.startswith("MATCH:"):
        template_name = decision.replace("MATCH:", "").strip()
        return {
            **state,
            "matched_template_name": template_name,
            "routing_decision": "found"
        }  

    return {
        **state,
        "routing_decision": "not_found"
    }  
