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

def create_templates_table(cursor, connection):
    try:
        # Drop the table if it exists
        cursor.execute('DROP TABLE IF EXISTS "Templates" CASCADE;')
        print("Dropped existing 'Templates' table (if any).")

        # Now create the table again
        cursor.execute('''
            CREATE TABLE "Templates" (
                "template_id" UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                "name" TEXT UNIQUE NOT NULL,
                "subject" TEXT NOT NULL,
                "content" TEXT NOT NULL
            );
        ''')
        connection.commit()
        print("Created new 'Templates' table with subject column.")
    except Exception as e:
        print(f"Error creating Templates table: {e}")



def insert_template(cursor, connection, name, subject, content):
    try:
        insert_query = '''
            INSERT INTO "Templates" ("name", "subject", "content")
            VALUES (%s, %s, %s)
            ON CONFLICT ("name") DO NOTHING
        '''
        cursor.execute(insert_query, (name, subject, content))
        connection.commit()
        print(f"Inserted template: {name}")
    except Exception as e:
        print(f"Error inserting template: {e}")


template_name = "password_expiry_reminder"
template_subject = "Your Password Will Expire in 5 Days"
template_content = """
Dear {{name}},

This is a reminder that your account password is set to expire in 5 days.

To maintain access to your account and ensure your security, please reset your password as soon as possible using the link below:

Reset Password: {{reset_link}}

If you have already updated your password, please disregard this message.

Thank you,
Support Team
"""



def main():
    connection = connect_to_postgres()
    if connection is None:
        return

    try:
        cursor = connection.cursor()
        # insert_random_users(cursor, connection, 10)
        # print_users(cursor, 20)
        create_password_reset_tokens_table(cursor, connection)
        create_templates_table(cursor, connection)
        insert_template(cursor, connection, template_name, template_subject, template_content)

    finally:
        cursor.close()
        connection.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()
