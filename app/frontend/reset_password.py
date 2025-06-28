import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="Reset Password", layout="centered")

st.title("🔐 Reset Your Password")

# Get token from URL parameters using the new method
token = st.query_params.get("token")

if not token:
    st.error("Invalid reset link. Please request a new password reset.")
    st.stop()

st.subheader("🔁 Enter Your New Password")

new_password = st.text_input("Enter new password", type="password")
confirm_password = st.text_input("Confirm new password", type="password")

if st.button("Reset Password"):
    if not new_password:
        st.error("Please enter a new password.")
    elif new_password != confirm_password:
        st.error("Passwords do not match.")
    elif len(new_password) < 6:
        st.warning("Password should be at least 6 characters.")
    else:
        try:
            payload = {
                "token": token,
                "new_password": new_password
            }
            response = requests.post(f"{BACKEND_URL}/reset-password", json=payload)
            if response.status_code == 200:
                st.success("✅ Password updated successfully. You can now log in with your new password.")
            else:
                st.error(response.json()["detail"])
        except Exception as e:
            st.error(f"❌ Failed to reset password: {str(e)}")
