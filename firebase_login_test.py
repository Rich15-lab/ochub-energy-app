import streamlit as st
import pyrebase

# 🔧 Load Firebase config from secrets.toml
firebase_config = st.secrets["FIREBASE"]
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# 🔐 Login screen
def login_page():
    st.set_page_config(page_title="OCHub Login", layout="centered")
    st.title("🔐 Login to OCHub")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            auth.sign_in_with_email_and_password(email, password)
            st.session_state["logged_in"] = True
            st.session_state["user_email"] = email
            st.success("✅ Login successful!")
            st.rerun()
        except:
            st.error("❌ Login failed. Please check your credentials.")

# 🧭 Dashboard if logged in
def dashboard():
    st.set_page_config(page_title="OCHub Dashboard", layout="wide")
    st.title("📊 OCHub Dashboard")
    st.write(f"Welcome, {st.session_state['user_email']}!")

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# 🚪 App controller
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if st.session_state["logged_in"]:
    dashboard()
else:
    login_page()
