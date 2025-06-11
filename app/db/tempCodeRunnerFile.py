import psycopg2
from psycopg2 import sql
import os
import random
import string
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
POSTGRES_URI = os.getenv("POSTGRES_URI")

def connect_to_postgres():
    try:
        connection = psycopg2.connect(POSTGRES_URI)
        print("✅ Connected to PostgreSQL.")
        return connection
    except Exception as e:
        print("❌ Connection failed:", e)
        return None
connect_to_postgres()