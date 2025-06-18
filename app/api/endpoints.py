from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2
import os
import secrets

from ..db.createdb import connect_to_postgres

load_dotenv()
POSTGRES_URI = os.getenv("POSTGRES_URI")

app = FastAPI()

class PasswordResetRequest(BaseModel):
    emp_num: int

class PasswordResetTokenRequest(BaseModel):
    token: str
    new_password: str


@app.post("/request-password-reset")
def request_password_reset(payload: PasswordResetRequest):
    connection = connect_to_postgres()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    
    try:
        cursor = connection.cursor()

        cursor.execute('SELECT * FROM "users" WHERE "emp_num" = %s', (payload.emp_num,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(minutes=30)

        cursor.execute(
            '''
            INSERT INTO "PasswordResetTokens" ("token", "emp_num", "expiry")
            VALUES (%s, %s, %s)
            ON CONFLICT ("token") DO NOTHING
            ''',
            (token, payload.emp_num, expiry)
        )
        connection.commit()

        reset_link = f"http://frontend/reset-password?token={token}"

        return {
            "message": "Reset link generated successfully.",
            "reset_link": reset_link
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        cursor.close()
        connection.close()



@app.post("/reset-password")
def reset_password(payload: PasswordResetTokenRequest):
    connection = connect_to_postgres()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    
    try:
        cursor = connection.cursor()

        cursor.execute(
            '''
            SELECT "emp_num", "expiry"
            FROM "PasswordResetTokens"
            WHERE "token" = %s
            ''',
            (payload.token,)
        )
        record = cursor.fetchone()

        if not record:
            raise HTTPException(status_code=404, detail="Invalid or expired token.")

        emp_num, expiry = record
        if datetime.now() > expiry:
            raise HTTPException(status_code=403, detail="Token has expired.")

        cursor.execute(
            '''
            UPDATE "users"
            SET "password" = %s, "last_update" = %s
            WHERE "emp_num" = %s
            ''',
            (payload.new_password, datetime.now(), emp_num)
        )

        cursor.execute(
            'DELETE FROM "PasswordResetTokens" WHERE "token" = %s',
            (payload.token,)
        )

        connection.commit()
        return {"message": "Password updated successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        cursor.close()
        connection.close()
