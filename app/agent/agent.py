from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

MYSQL_USER = os.getenv("SQL_USER")
MYSQL_PASSWORD = os.getenv("SQL_PASSWORD")  
MYSQL_HOST = "localhost"
MYSQL_PORT = "3306"
MYSQL_DB = "email_db"

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0,
    google_api_key=gemini_api_key
)

db_url = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
db = SQLDatabase.from_uri(db_url)

system_message = (
    "You are a helpful AI agent interacting with a SQL database. "
    "Return all results as Python lists, formatted like ['email1', 'email2'] "
    "without any additional text or explanation."
)

toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent_executor = create_sql_agent(llm=llm, toolkit=toolkit, verbose=True, system_message = system_message)

response = agent_executor.invoke("list the emails of all users?")
print("\n📤 Response from LangChain Agent:\n", response)
