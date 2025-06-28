from agent.nodes.shared import AgentState

def approve_template(state: AgentState) -> AgentState:
    """
    This function is now designed to work with Streamlit frontend.
    The approval decision should be set by the frontend before calling this.
    For CLI usage, it will prompt for input.
    """
    
    generated_template = state.get("template", {})
    print("\n🔍 Generated Template:")
    print(f"Subject: {generated_template.get('subject', 'N/A')}")
    print(f"Content: {generated_template.get('content', 'N/A')}")
    
    # Check if approval decision was already set by frontend
    approval_decision = state.get("approval_decision", "")
    
    if approval_decision == "approved":
        print("✅ Template approved via frontend.")
        return {
            **state,
            "approval_decision": "approved"
        }
    elif approval_decision == "refine":
        print("🔁 Refining template based on frontend feedback...")
        return {
            **state,
            "approval_decision": "refine"
        }
    else:
        # For CLI usage - prompt for input
        print("\nWould you like to use this template? Type 'yes' to approve, or type feedback to refine it.")
        feedback = input("Your response: ").strip()
        
        if feedback.lower() in ["yes", "y", "approve"]:
            print("✅ Template approved.")
            return {
                **state,
                "approval_decision": "approved"
            }
        else:
            print("🔁 Refining template based on feedback...")
            return {
                **state,
                "template_feedback": feedback,
                "approval_decision": "refine"
            }
