from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from agent.nodes.shared import AgentState
from agent.sql_agent import agent_executor
import ast
import os

load_dotenv()
gemini_api_key2 = os.getenv("GEMINI_API_KEY2")

llm = ChatGoogleGenerativeAI(  
    model="gemini-1.5-flash",
    temperature=0,
    google_api_key=gemini_api_key2
)

def generate_template(state: AgentState) -> AgentState:
    intent = state.get("query_intent", "remind users their password will expire soon")
    feedback = state.get("template_feedback", "")
    
    prompt = f"""
You are an email template generator. Create professional HTML email templates.

CRITICAL FORMATTING RULES:
1. DO NOT wrap your response in markdown code blocks (no ```html or ```
2. DO NOT use any markdown formatting in your response
3. Output raw HTML only - no backticks, no code block markers
4. Use ONLY these variables when needed: {{{{user}}}} and {{{{reset_link}}}}
5. Variables must be in curly braces: {{{{variable_name}}}}
6. Use {{{{user}}}} for the recipient's name
7. Use {{{{reset_link}}}} ONLY if the email involves password reset, password change, or account recovery

IMPORTANT RULES:
1. Use ONLY these variables when needed: {{user}} and {{reset_link}}
2. Variables must be in curly braces: {{variable_name}}
3. Use {{user}} for the recipient's name
4. Use {{reset_link}} ONLY if the email involves password reset, password change, or account recovery
5. Generate the content in HTML format with proper HTML tags
6. Keep the template professional and well-formatted

TEMPLATE FORMAT:
Subject: [Your subject line]
Body: [Your HTML email content with proper tags like <p>, <br>, <strong>, etc.]

USER REQUEST: {intent}
{f'FEEDBACK TO INCORPORATE: {feedback}' if feedback else ''}

Generate an HTML email template. Use HTML tags for formatting (paragraphs, line breaks, bold text, etc.).
"""

    response = llm.invoke(prompt)
    template_text = response.content if hasattr(response, 'content') else str(response)
    
    lines = template_text.strip().split('\n')
    subject = ""
    body = ""
    
    for i, line in enumerate(lines):
        if line.startswith("Subject:"):
            subject = line.replace("Subject:", "").strip()
            body = '\n'.join(lines[i+1:]).strip()
            break
    
    if body.startswith("Body:"):
        body = body.replace("Body:", "").strip()
    
    state["template"] = {
        "subject": subject,
        "content": body  
    }
    
    state.pop("template_feedback", None)
    return state