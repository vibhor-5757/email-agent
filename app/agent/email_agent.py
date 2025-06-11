from langgraph.graph import StateGraph, END
from typing import List, TypedDict
import ast
from sql_agent import agent_executor

class AgentState(TypedDict):
    emails: List[str]

import ast

def extract_emails(state: AgentState) -> AgentState:
    query = """
    List the emails of users from the "users" table whose passwords are about to expire in 5 days.
    The password expiration time is calculated using the "last_update" column, and the expiration period in days
    is stored in the "constants" table under the column "value" for the row with Name = 'password_change_frequency'.
    """
    response = agent_executor.invoke(query)
    print("\nExtracted Agent Response:\n", response)

    if isinstance(response, list):
        emails = response
    elif isinstance(response, dict) and "output" in response:
        output = response["output"]
        if isinstance(output, str):
            try:
                emails = ast.literal_eval(output)
            except (SyntaxError, ValueError):
                emails = []
        else:
            emails = output
    else:
        emails = []

    return {**state, "emails": emails}

def send_emails(state: AgentState) -> AgentState:
    predefined_content = (
        "Subject: Password Expiry Alert\n\n"
        "Your password is about to expire in 5 days. Please update it to maintain account security."
    )
    emails = state["emails"]
    print("\nSending Emails:")
    for email in emails:
        print(f"To: {email}\n{predefined_content}\n{'-' * 50}")
    return state

graph = StateGraph(AgentState)
graph.add_node("extract_emails", extract_emails)
graph.add_node("send_emails", send_emails)

graph.set_entry_point("extract_emails")
graph.add_edge("extract_emails", "send_emails")
graph.set_finish_point("send_emails")

app = graph.compile()

app.invoke({})
