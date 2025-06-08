import mysql.connector
from mysql.connector import errorcode
import os
from dotenv import load_dotenv

load_dotenv()

MYSQL_HOST = "localhost"
MYSQL_USER = os.getenv("SQL_USER")
MYSQL_PASSWORD = os.getenv("SQL_PASSWORD")  

def connect_to_mysql():
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        print("Connected to MySQL server.")
        return connection
    
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None

def create_database(cursor, db_name="email_db"):
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        print(f"Database '{db_name}' created or already exists.")
        cursor.execute(f"USE {db_name}")
    except mysql.connector.Error as err:
        print(f"Error creating database: {err}")

def create_users_table(cursor):
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(255) UNIQUE
            )
        """)
        print("Table 'users' created or already exists.")
    except mysql.connector.Error as err:
        print(f"Error creating table: {err}")

def insert_users(cursor, connection):
    try:
        insert_query = """
            INSERT INTO users (name, email)
            VALUES (%s, %s)
        """
        values = [
            ('vibhor', 'vibhor.1bhatia@gmail.com')
        ]
        cursor.executemany(insert_query, values)
        connection.commit()
        print("user data inserted.")
    except mysql.connector.Error as err:
        print(f"Error inserting data: {err}")

def print_first_10_users(cursor):
    try:
        cursor.execute("SELECT * FROM users LIMIT 10")
        rows = cursor.fetchall()
        
        if not rows:
            print("No users found in the table.")
            return

        for row in rows:
            print(f"ID: {row[0]} \t Name: {row[1]} \t Email: {row[2]}")

    except mysql.connector.Error as err:
        print(f"Error fetching users: {err}")

def main():
    connection = connect_to_mysql()
    if connection is None:
        return

    try:
        cursor = connection.cursor()
        create_database(cursor)
        create_users_table(cursor)
        insert_users(cursor, connection)
        print_first_10_users(cursor)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed.")

if __name__ == "__main__":
    main()
