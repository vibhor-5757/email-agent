# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from datetime import datetime, timedelta
# from dotenv import load_dotenv
# import psycopg2
# import os
# import secrets

# from ..db.createdb import connect_to_postgres

# load_dotenv()
# POSTGRES_URI = os.getenv("POSTGRES_URI")

# app = FastAPI()

# class PasswordResetRequest(BaseModel):
#     emp_num: int

# class PasswordResetTokenRequest(BaseModel):
#     token: str
#     new_password: str


# @app.post("/request-password-reset")
# def request_password_reset(payload: PasswordResetRequest):
#     connection = connect_to_postgres()
#     if connection is None:
#         raise HTTPException(status_code=500, detail="Database connection failed.")
    
#     try:
#         cursor = connection.cursor()

#         cursor.execute('SELECT * FROM "users" WHERE "emp_num" = %s', (payload.emp_num,))
#         user = cursor.fetchone()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found.")

#         token = secrets.token_urlsafe(32)
#         expiry = datetime.now() + timedelta(minutes=30)

#         cursor.execute(
#             '''
#             INSERT INTO "PasswordResetTokens" ("token", "emp_num", "expiry")
#             VALUES (%s, %s, %s)
#             ON CONFLICT ("token") DO NOTHING
#             ''',
#             (token, payload.emp_num, expiry)
#         )
#         connection.commit()

#         reset_link = f"http://frontend/reset-password?token={token}"

#         return {
#             "message": "Reset link generated successfully.",
#             "reset_link": reset_link
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
#     finally:
#         cursor.close()
#         connection.close()



# @app.post("/reset-password")
# def reset_password(payload: PasswordResetTokenRequest):
#     connection = connect_to_postgres()
#     if connection is None:
#         raise HTTPException(status_code=500, detail="Database connection failed.")
    
#     try:
#         cursor = connection.cursor()

#         cursor.execute(
#             '''
#             SELECT "emp_num", "expiry"
#             FROM "PasswordResetTokens"
#             WHERE "token" = %s
#             ''',
#             (payload.token,)
#         )
#         record = cursor.fetchone()

#         if not record:
#             raise HTTPException(status_code=404, detail="Invalid or expired token.")

#         emp_num, expiry = record
#         if datetime.now() > expiry:
#             raise HTTPException(status_code=403, detail="Token has expired.")

#         cursor.execute(
#             '''
#             UPDATE "users"
#             SET "password" = %s, "last_update" = %s
#             WHERE "emp_num" = %s
#             ''',
#             (payload.new_password, datetime.now(), emp_num)
#         )

#         cursor.execute(
#             'DELETE FROM "PasswordResetTokens" WHERE "token" = %s',
#             (payload.token,)
#         )

#         connection.commit()
#         return {"message": "Password updated successfully."}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
#     finally:
#         cursor.close()
#         connection.close()
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2
import os
import secrets
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from ..db.createdb import connect_to_postgres

load_dotenv()
POSTGRES_URI = os.getenv("POSTGRES_URI")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")  # Your verified sender email in SendGrid
# print(FROM_EMAIL)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8502")

app = FastAPI()

class PasswordResetRequest(BaseModel):
    emp_num: int

class PasswordResetTokenRequest(BaseModel):
    token: str
    new_password: str

def send_reset_email_sendgrid(to_email: str, reset_link: str):
    """Send password reset email using SendGrid (currently disabled)"""
    try:
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=to_email,
            subject='Password Reset Request',
            html_content=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2>Password Reset Request</h2>
                <p>Hello,</p>
                <p>You have requested to reset your password. Please click on the button below to reset your password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" 
                       style="background-color: #007bff; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                <p>Or copy and paste this link in your browser:</p>
                <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 4px;">
                    {reset_link}
                </p>
                <p><strong>This link will expire in 30 minutes.</strong></p>
                <p>If you did not request this password reset, please ignore this email.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">Best regards,<br>Your IT Team</p>
            </div>
            """
        )
        
        sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
        response = sg.send(message)
        
        print(f"SendGrid Response Status Code: {response.status_code}")
        return True
        
    except Exception as e:
        print(f"Failed to send email via SendGrid: {str(e)}")
        return False

@app.post("/request-password-reset")
def request_password_reset(payload: PasswordResetRequest):
    connection = connect_to_postgres()
    if connection is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    
    try:
        cursor = connection.cursor()

        cursor.execute('SELECT "email" FROM "users" WHERE "emp_num" = %s', (payload.emp_num,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        user_email = user[0]
        token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(minutes=30)

        cursor.execute('DELETE FROM "PasswordResetTokens" WHERE "emp_num" = %s', (payload.emp_num,))

        cursor.execute(
            '''
            INSERT INTO "PasswordResetTokens" ("token", "emp_num", "expiry")
            VALUES (%s, %s, %s)
            ''',
            (token, payload.emp_num, expiry)
        )
        connection.commit()

        reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
        
        print("=" * 50)
        print("PASSWORD RESET LINK GENERATED")
        print("=" * 50)
        print(f"Employee Number: {payload.emp_num}")
        print(f"Email: {user_email}")
        print(f"Reset Link: {reset_link}")
        print(f"Token: {token}")
        print(f"Expires: {expiry}")
        print("=" * 50)

        if send_reset_email_sendgrid(user_email, reset_link):
            return {"message": "Reset link sent to your email successfully."}
        else:
            raise HTTPException(status_code=500, detail="Failed to send reset email.")

        # return {
        #     "message": "Reset link generated successfully (email sending disabled for testing).",
        #     "reset_link": reset_link,
        #     "email": user_email,
        #     "expires_in_minutes": 30
        # }

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
            # Clean up expired token
            cursor.execute('DELETE FROM "PasswordResetTokens" WHERE "token" = %s', (payload.token,))
            connection.commit()
            raise HTTPException(status_code=403, detail="Token has expired.")

        # Update password (Note: In production, hash the password before storing)
        cursor.execute(
            '''
            UPDATE "users"
            SET "password" = %s, "last_update" = %s
            WHERE "emp_num" = %s
            ''',
            (payload.new_password, datetime.now(), emp_num)
        )

        # Delete used token
        cursor.execute(
            'DELETE FROM "PasswordResetTokens" WHERE "token" = %s',
            (payload.token,)
        )

        connection.commit()
        
        print(f"Password successfully reset for employee: {emp_num}")
        
        return {"message": "Password updated successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        cursor.close()
        connection.close()
