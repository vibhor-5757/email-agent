from typing import List, TypedDict, Optional

class AgentState(TypedDict, total=False):
    emails: List[str]
    template: dict
    matched_template_name: str
    query_intent: str
    template_feedback: str
    routing_decision: str  
    approval_decision: str

