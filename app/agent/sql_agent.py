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


llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0,
    google_api_key=gemini_api_key
)

db = SQLDatabase.from_uri(POSTGRES_URI,  include_tables=["users", "constants"])

system_message = (
    "You are a helpful AI agent interacting with a PostgreSQL database. "
    "IMPORTANT: Return only plain SQL code without any markdown formatting, "
    "triple backticks, or code block delimiters. "
    "Do not wrap SQL in ```sql or ```"
    "Return raw SQL queries that can be executed directly. "
    "For final answers, return results as Python lists like ['email1', 'email2'] with no extra explanation."
)


original_run = SQLDatabase.run

def safe_run(self, command: str, fetch: str = "all", **kwargs):
    command = re.sub(r"^```sql\s*|^```", "", command.strip(), flags=re.IGNORECASE)
    command = re.sub(r"```$", "", command.strip())
    command = command.replace("```", "").replace("`", "")
    command = command.strip()

    print(f"\nCleaned SQL command:\n{command}\n{'-' * 50}")

    return original_run(self, command, fetch=fetch, **kwargs)

SQLDatabase.run = safe_run

toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=False,
    system_message=system_message
)

if __name__=="__main__":
    query = """
    List the emails of users from the "users" table whose passwords are about to expire in 5 days.
    The password expiration time is calculated using the "last_update" column, and the expiration period in days
    is stored in the "constants" table under the column "value" for the row with Name = 'password_change_frequency'.
    """

    response = agent_executor.invoke(query)
    print("\nResponse from LangChain Agent:\n", response)
