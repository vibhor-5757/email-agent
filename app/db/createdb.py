import psycopg2
from psycopg2 import sql
import os
import random
import string
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
POSTGRES_URI = os.getenv("POSTGRES_URI")

def connect_to_postgres():
    try:
        connection = psycopg2.connect(POSTGRES_URI)
        print("Connected to Supabase.")
        return connection
    except Exception as e:
        print("Connection failed:", e)
        return None

def print_users(cursor, n=10):
    try:
        cursor.execute(f'SELECT "EmpNum", "Name", "Email" FROM "Users" LIMIT {n}')
        rows = cursor.fetchall()
        if not rows:
            print("No users found.")
            return
        for row in rows:
            print(f"EmpNum: {row[0]} \t Name: {row[1]} \t Email: {row[2]}")
    except Exception as e:
        print(f"Error fetching users: {e}")

def generate_random_user():
    # Generate a random date in the range 01-05-2025 to 11-05-2025
    start_date = datetime(2025, 5, 1)
    end_date = datetime(2025, 6, 11)
    delta_days = (end_date - start_date).days
    random_days = random.randint(0, delta_days)
    last_update = start_date + timedelta(days=random_days)

    name = ''.join(random.choices(string.ascii_letters, k=6))
    email = f"{name.lower()}@example.com"
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    return (last_update, name, email, password)


def insert_random_users(cursor, connection, n=10):
    try:
        insert_query = '''
            INSERT INTO "Users" ("LastUpdate", "Name", "Email", "Password")
            VALUES (%s, %s, %s, %s)
            ON CONFLICT ("Email") DO NOTHING
        '''
        users = [generate_random_user() for _ in range(n)]
        cursor.executemany(insert_query, users)
        connection.commit()
        print(f"Inserted {n} random users.")
    except Exception as e:
        print(f"Error inserting users: {e}")

def create_password_reset_tokens_table(cursor, connection):
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS "PasswordResetTokens" (
                "token" TEXT PRIMARY KEY,
                "emp_num" INTEGER NOT NULL REFERENCES "users"("emp_num") ON DELETE CASCADE,
                "expiry" TIMESTAMP NOT NULL
            );
        ''')
        connection.commit()
        print("Checked or created table 'PasswordResetTokens'.")
    except Exception as e:
        print(f"Error creating PasswordResetTokens table: {e}")

def main():
    connection = connect_to_postgres()
    if connection is None:
        return

    try:
        cursor = connection.cursor()
        # insert_random_users(cursor, connection, 10)
        # print_users(cursor, 20)
        create_password_reset_tokens_table(cursor, connection)
    finally:
        cursor.close()
        connection.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()
