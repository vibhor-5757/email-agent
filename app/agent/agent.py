from langgraph.graph import StateGraph, END
from agent.nodes.shared import AgentState
from agent.nodes.extract_email import extract_emails
from agent.nodes.match_template import match_existing_template
from agent.nodes.load_template import load_template_by_name
from agent.nodes.generate_template import generate_template
from agent.nodes.approve_template import approve_template
from agent.nodes.store_template import store_template
from agent.nodes.send_emails import send_emails

def route_template_matching(state: AgentState) -> str:
    return state.get("routing_decision", "not_found")

def route_approval(state: AgentState) -> str:
    return state.get("approval_decision", "refine")

graph = StateGraph(AgentState)

graph.add_node("extract_emails", extract_emails)
graph.add_node("match_template", match_existing_template)  
graph.add_node("load_template", load_template_by_name)
graph.add_node("generate_template", generate_template)
graph.add_node("approve_template", approve_template)
graph.add_node("store_template", store_template)
graph.add_node("send_emails", send_emails)

graph.set_entry_point("extract_emails")

graph.add_edge("extract_emails", "match_template")

graph.add_conditional_edges("match_template", route_template_matching, {
    "found": "load_template",
    "not_found": "generate_template"
})

graph.add_edge("load_template", "send_emails")
graph.add_edge("generate_template", "approve_template")

graph.add_conditional_edges("approve_template", route_approval, {
    "approved": "store_template", 
    "refine": "generate_template"
})

graph.add_edge("store_template", "send_emails")
graph.set_finish_point("send_emails")

app = graph.compile()


mermaid_str = app.get_graph().draw_mermaid()

if __name__ == "__main__":
    app.invoke({"query_intent": "email the users whoose password is less than 3 characters to increase the length of their password for better security"})
    