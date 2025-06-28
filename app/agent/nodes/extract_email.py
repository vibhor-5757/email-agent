from agent.nodes.shared import AgentState
from agent.sql_agent import agent_executor
import ast

def extract_emails(state: AgentState) -> AgentState:
    if state.get("query_intent") and state["query_intent"].strip():
        query = state["query_intent"]
        print(f"Using provided query: {query}")
    else:
        query = """
        List the emails of users from the "users" table whose passwords are about to expire in 5 days.
        The password expiration time is calculated using the "last_update" column, and the expiration period in days
        is stored in the "constants" table under the column "value" for the row with Name = 'password_change_frequency'.
        """
        state["query_intent"] = query
    result = agent_executor.invoke(query)
    
    try:
        output = result.get("output", "")
        if output.startswith('[') and output.endswith(']'):
            emails = ast.literal_eval(output)
        else:
            emails = [email.strip() for email in output.split(',') if email.strip()]
    except:
        emails = []

    return {**state, "emails": emails}
