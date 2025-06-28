from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import re
from dotenv import load_dotenv

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
POSTGRES_URI = os.getenv("POSTGRES_URI")
print(gemini_api_key)

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0,
    google_api_key=gemini_api_key
)

db = SQLDatabase.from_uri(POSTGRES_URI)

system_message = (
    "You are a helpful AI agent interacting with a PostgreSQL database. "
    "IMPORTANT: You are never to use the keyword LIMIT in your sql queries. "
    
    "CRITICAL BUSINESS LOGIC:\n"
    "- Password expiration is NOT a single column - it's calculated!\n"
    "- Password expires when: users.last_update + INTERVAL (constants.value || ' days')\n"
    "- ALWAYS join users with constants where constants.Name = 'password_change_frequency'\n"
    "- users.last_update = when password was last changed\n"
    "- constants.value (where Name='password_change_frequency') = expiration period in days\n"
    
    "MANDATORY QUERY PATTERN for password expiration:\n"
    "SELECT u.email FROM users u "
    "CROSS JOIN constants c "
    "WHERE c.Name = 'password_change_frequency' "
    "AND u.last_update + INTERVAL (c.value || ' days') <= CURRENT_DATE + INTERVAL 'X days'\n"
    
    "TABLE DETAILS:\n"
    "- users: emp_num, last_update (password change date), name, email, password\n"
    "- constants: Name (key), value (configuration value)\n"
    "- PasswordResetTokens: password reset tokens\n"
    "- email_templates: email template storage\n"
    
    "For final answers, return results as Python lists like ['email1', 'email2'] with no extra explanation."
)

custom_prefix = """You are an agent designed to interact with a SQL database.

IMPORTANT SCHEMA RELATIONSHIPS:
- Password expiration is calculated, not stored directly
- Formula: users.last_update + INTERVAL (constants.value || ' days')
- constants table contains 'password_change_frequency' setting

REQUIRED QUERY PATTERNS:

For password expiration queries, ALWAYS use this pattern:
SELECT u.email
FROM users u
CROSS JOIN constants c
WHERE c.Name = 'password_change_frequency'
AND u.last_update + INTERVAL (c.value || ' days') <= CURRENT_DATE + INTERVAL 'N days'
Given an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results.

NEVER assume password expiration is a direct column - it's always calculated from last_update + constants.value.

You have access to tools for interacting with the database.
Only use the below tools. Only use the information returned by the below tools to construct your final answer.
You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

IMPORTANT: You are allowed to perform INSERT operations when explicitly requested to save or store data.
DO NOT make UPDATE, DELETE, or DROP statements to the database.
For SELECT queries, do not use the LIMIT keyword.

If the question does not seem related to the database, just return "I don't know" as the answer.

For final answers, return results as Python lists like ['email1', 'email2'] with no extra explanation.
The python square braackets indicating a list must be present
"""



original_run = SQLDatabase.run

def safe_run(self, command: str, fetch: str = "all", **kwargs):
    command = re.sub(r"^```sql\s*|^```", "", command.strip(), flags=re.IGNORECASE)
    command = re.sub(r"```$", "", command.strip())
    command = command.replace("```", "").replace("`", "")
    command = command.strip()

    print(f"\nCleaned SQL command:\n{command}\n{'-' * 50}")

    return original_run(self, command, fetch=fetch, **kwargs)

SQLDatabase.run = safe_run

from langchain.tools import tool

@tool
def get_schema_info(table_name: str) -> str:
    """Get schema relationships and common patterns for a table"""
    schema_patterns = {
        "users": "Email column: users.email. Password tracking: users.last_update. For expiration: JOIN with constants table",
        "constants": "Key-value store. Name='password_change_frequency' contains expiration days. Use: WHERE Name = 'password_change_frequency'",
        "template": "Email templates storage",
        "token": "Authentication tokens"
    }
    return schema_patterns.get(table_name, "Table not found")

@tool  
def get_query_pattern(domain: str) -> str:
    """Get SQL patterns for common operations"""
    patterns = {
        "password_expiration": "users.last_update + INTERVAL (constants.value || ' days') WHERE constants.Name = 'password_change_frequency'",
        "user_emails": "SELECT email FROM users",
        "system_config": "SELECT value FROM constants WHERE Name = 'config_key'"
    }
    return patterns.get(domain, "Pattern not found")

# Add to your existing toolkit
custom_tools = [get_schema_info, get_query_pattern]
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
all_tools = toolkit.get_tools() + custom_tools

# Update your agent creation
agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    top_k=1000000,
    system_message=system_message,
    prefix=custom_prefix,
    extra_tools=custom_tools  # Add this line
)


if __name__=="__main__":
    query = """
    List the emails of users from the "users" table whose passwords are about to expire in 5 days.
    
    """

    response = agent_executor.invoke(query)
    print("\nResponse from LangChain Agent:\n", response)
