import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"  # change this to your deployed FastAPI base URL

st.set_page_config(page_title="Password Reset Request", layout="centered")

st.title("Password Reset Portal")

st.subheader("Request Reset Link")
# st.write("Enter your Employee Number to receive a password reset link via email.")

emp_num = st.number_input("Enter your Employee Number", step=1, format="%d")

if st.button("Request Reset Link"):
    try:
        response = requests.post(f"{BACKEND_URL}/request-password-reset", json={"emp_num": emp_num})
        if response.status_code == 200:
            st.success("✅ Password reset link has been sent to your registered email address.")
            st.info("Please check your email and click on the reset link to set your new password.")
        else:
            st.error(response.json()["detail"])
    except Exception as e:
        st.error(f"❌ Failed to request reset link: {str(e)}")
