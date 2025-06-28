import streamlit as st
import sys
import os
from typing import Dict, Any
import datetime

# Add the path to your agent modules
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "../"))
sys.path.insert(0, ROOT_DIR)

# try:
from agent.agent import app as langgraph_app
from agent.nodes.shared import AgentState

if "agent_state" not in st.session_state:
    st.session_state.agent_state = None
if "stage" not in st.session_state:
    st.session_state.stage = "input"
if "template_approved" not in st.session_state:
    st.session_state.template_approved = False

st.set_page_config(
    page_title="Email Template Agent",
    page_icon="",
    layout="wide"
)

st.title("Email Template Agent")
st.markdown("Generate and send customized email templates to users based on your query.")

# Stage 1: Query Input
if st.session_state.stage == "input":
    st.header("🔍 Enter Your Query")
    
    st.markdown("**Example queries:**")
    st.markdown("- Email users whose passwords will expire in 5 days")
    st.markdown("- Email users whose password is less than 15 characters to increase length")
    st.markdown("- Remind users to update their profile information")
    
    query = st.text_area(
        "Enter your email query:",
        height=100,
        placeholder="Describe what kind of email you want to send and to whom..."
    )
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("Send Emails", type="primary", disabled=not query.strip()):
            with st.spinner("Extracting emails and generating template..."):
                try:
                    from agent.nodes.extract_email import extract_emails
                    from agent.nodes.match_template import match_existing_template
                    from agent.nodes.load_template import load_template_by_name
                    from agent.nodes.generate_template import generate_template
                    
                    state = {"query_intent": query}
                    
                    state = extract_emails(state)
                    st.info(f"Found {len(state.get('emails', []))} recipients")
                    
                    state = match_existing_template(state)
                    
                    if state.get("routing_decision") == "found":
                        state = load_template_by_name(state)
                        st.info(f"Loaded existing template: {state.get('matched_template_name')}")
                    else:
                        state = generate_template(state)
                        st.info("Generated new template")
                    
                    st.session_state.agent_state = state
                    st.session_state.stage = "approve"
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error running agent: {str(e)}")
                    st.exception(e)
    
    with col2:
        if st.button("🔄 Clear"):
            st.session_state.clear()
            st.rerun()

elif st.session_state.stage == "approve":
    state = st.session_state.agent_state
    
    st.header("📋 Template Review & Approval")
    
    # Show extracted emails
    if "emails" in state and state["emails"]:
        st.subheader(f"Target Recipients ({len(state['emails'])} users)")
        with st.expander("View recipient emails"):
            for i, email in enumerate(state["emails"], 1):
                st.write(f"{i}. {email}")
    else:
        st.warning("No emails were extracted for your query.")
        if st.button("← Back to Query"):
            st.session_state.stage = "input"
            st.rerun()
        st.stop()
    
    if "template" in state and state["template"]:
        st.subheader("📝 Generated Email Template")
        
        template = state["template"]
        
        st.markdown("**Subject:**")
        st.info(template.get("subject", "No subject"))
        
        st.markdown("**Content:**")
        content = template.get('content', 'No content')
        
        if '<' in content and '>' in content:
            st.markdown(content, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="
                background-color: #f0f2f6; 
                padding: 20px; 
                border-radius: 10px; 
                border-left: 5px solid #1f77b4;
                margin: 10px 0;
                white-space: pre-wrap;
            ">
                {content}
            </div>
            """, unsafe_allow_html=True)
        
        if "{user}" in content or "{reset_link}" in content:
            st.markdown("**Variables that will be replaced:**")
            variables = []
            if "{user}" in content:
                variables.append("• `{user}` → Recipient's name from database")
            if "{reset_link}" in content:
                variables.append("• `{reset_link}` → Password reset link")
            
            for var in variables:
                st.markdown(var)
        
        st.markdown("---")
        st.subheader("✅ Review & Decision")
        
        col1, col2, col3 = st.columns([2, 2, 3])
        
        with col1:
            if st.button("✅ Approve & Send", type="primary", use_container_width=True):
                # Set approval decision in state
                current_state = st.session_state.agent_state
                current_state["approval_decision"] = "approved"
                st.session_state.agent_state = current_state
                st.session_state.template_approved = True
                st.session_state.stage = "results"
                st.rerun()
        
        with col2:
            if st.button("❌ Reject & Regenerate", use_container_width=True):
                st.session_state.stage = "feedback"
                st.rerun()
        
        with col3:
            if st.button("← Back to Query", use_container_width=True):
                st.session_state.stage = "input"
                st.rerun()
    
    else:
        st.error("No template was generated.")
        if st.button("← Back to Query"):
            st.session_state.stage = "input"
            st.rerun()

elif st.session_state.stage == "feedback":
    st.header("💬 Provide Feedback")
    st.markdown("Please provide feedback on how to improve the template:")
    
    feedback = st.text_area(
        "Your feedback:",
        height=150,
        placeholder="E.g., Make it more formal, add urgency, include specific instructions..."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Regenerate with Feedback", type="primary", disabled=not feedback.strip()):
            with st.spinner("Regenerating template with your feedback..."):
                try:
                    from agent.nodes.generate_template import generate_template
                    
                    current_state = st.session_state.agent_state
                    current_state["template_feedback"] = feedback
                    current_state["approval_decision"] = "refine"
                    
                    # Regenerate template with feedback
                    updated_state = generate_template(current_state)
                    st.session_state.agent_state = updated_state
                    st.session_state.stage = "approve"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error regenerating template: {str(e)}")
                    st.exception(e)
    
    with col2:
        if st.button("← Back to Template"):
            st.session_state.stage = "approve"
            st.rerun()

# Stage 3: Results
elif st.session_state.stage == "results":
    if st.session_state.template_approved:
        st.header("🎉 Processing...")
        
        progress_container = st.container()
        
        with st.spinner("Storing template and sending emails..."):
            try:
                from agent.nodes.store_template import store_template
                from agent.nodes.send_emails import send_emails
                
                state = st.session_state.agent_state
                
                # Set template name if not already set
                if not state.get("matched_template_name"):
                    template_name = f"template_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    state["matched_template_name"] = template_name
                
                # Store the template
                with progress_container:
                    st.info("📝 Saving template to database...")
                updated_state = store_template(state)
                
                # Send emails
                with progress_container:
                    st.info("📧 Sending emails...")
                final_state = send_emails(updated_state)
                
                st.session_state.agent_state = final_state
                
            except Exception as e:
                st.error(f"Error during execution: {str(e)}")
                st.exception(e)
                st.stop()
        
        # Clear progress messages and show success
        progress_container.empty()
        st.success("✅ Process Completed Successfully!")
        
        state = st.session_state.agent_state
        
        # Results summary
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                label="Emails Sent",
                value=len(state.get("emails", []))
            )
        
        with col2:
            st.metric(
                label="📝 Template Saved",
                value=state.get("matched_template_name", "Unknown")
            )
        
        # Show final template used
        st.subheader("📋 Final Template Used")
        template = state.get("template", {})
        
        with st.expander("View Template Details"):
            st.markdown(f"**Subject:** {template.get('subject', 'N/A')}")
            st.markdown("**Content:**")
            content = template.get('content', 'N/A')
            if '<' in content and '>' in content:
                st.markdown(content, unsafe_allow_html=True)
            else:
                st.code(content)
        
        # Show recipient list
        with st.expander(f"View Recipients ({len(state.get('emails', []))} users)"):
            emails = state.get("emails", [])
            if emails:
                # Display in columns for better layout
                cols = st.columns(3)
                for i, email in enumerate(emails):
                    with cols[i % 3]:
                        st.write(f"{i+1}. {email}")
            else:
                st.write("No recipients found")
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Create New Template", type="primary"):
                st.session_state.clear()
                st.rerun()
        
        with col2:
            if st.button("View Details", type="secondary"):
                st.json(state)

# Sidebar with info
with st.sidebar:
    st.header("ℹ️ How it works")
    st.markdown("""
    1. **Enter Query**: Describe what emails you want to send
    2. **Review Template**: Check the generated template
    3. **Approve/Provide Feedback**: Accept or improve the template
    4. **Send Emails**: Template is saved and emails are sent
    """)
    
    st.header("🔧 Current Stage")
    stages = {
        "input": "🔍 Query Input",
        "approve": "📋 Template Approval", 
        "feedback": "💬 Providing Feedback",
        "results": "🎉 Results"
    }
    st.info(stages.get(st.session_state.stage, "Unknown"))
    
    if st.session_state.agent_state:
        st.header("📊 Current State")
        with st.expander("View Agent State"):
            st.json(st.session_state.agent_state)

# Add error boundary
if st.session_state.get("error"):
    st.error("An error occurred. Please refresh the page and try again.")
    if st.button("🔄 Reset Application"):
        st.session_state.clear()
        st.rerun()
