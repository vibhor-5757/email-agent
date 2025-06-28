from agent.nodes.shared import AgentState
import os
import psycopg2
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")
FRONTEND_LINK = os.getenv("FRONTEND_LINK1")
POSTGRES_URI = os.getenv("POSTGRES_URI")

def connect_to_postgres():
    try:
        connection = psycopg2.connect(POSTGRES_URI)
        return connection
    except Exception as e:
        print("Connection failed:", e)
        return None

def send_emails(state: AgentState) -> AgentState:
    print("WE ARE IN SEND EMAILS: ")
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    
    subject = state["template"].get("subject", "")
    content = state["template"].get("content", "")
    
    connection = connect_to_postgres()
    if not connection:
        print("Failed to connect to database")
        return state
    
    cursor = connection.cursor()
    
    for email in state["emails"]:
        try:
            cursor.execute("SELECT name FROM users WHERE email = %s;", (email,))
            result = cursor.fetchone()
            
            user_name = result[0] if result else "User"
            print(f"User name for {email}: {user_name}")
            
            filled_content = content.replace("{user}", user_name)
            
            if "{reset_link}" in filled_content:
                filled_content = filled_content.replace("{reset_link}", FRONTEND_LINK)
            
            message = Mail(
                from_email=FROM_EMAIL,
                to_emails=email,
                subject=subject,
                html_content=filled_content
            )
            
            response = sg.send(message)
            
            if response.status_code == 202:
                print(f"✅ Email sent successfully to {email}")
            else:
                print(f"❌ Failed to send email to {email}. Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error sending email to {email}: {str(e)}")
    
    cursor.close()
    connection.close()
    return state

dummy_state: AgentState = {
    "emails": ["wang.1haochess@gmail.com"],
    "template": {
        "subject": "Password Security Update Required",
        "content": """Dear {user},

We noticed that your current password is shorter than our recommended security standards. To ensure your account remains secure, please update your password to be at least 15 characters long.

You can update your password by clicking the link below:
{reset_link}

If you have any questions, please don't hesitate to contact our IT support team.

Best regards,
IT Security Team"""
    },
    "query_intent": "email the users whose password is less than 15 characters to increase the length of their password for better security",
    "matched_template_name": "",
    "template_feedback": "",
    "routing_decision": ""
}

if __name__ == "__main__":
    print("Testing send_emails function with dummy data...")
    print(f"Target email: {dummy_state['emails'][0]}")
    print(f"Subject: {dummy_state['template']['subject']}")
    print("-" * 50)
    
    result_state = send_emails(dummy_state)
    print("\nTest completed!")