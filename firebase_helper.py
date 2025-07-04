import pyrebase
import streamlit as st

def init_firebase():
    config = {
        "apiKey": st.secrets["FIREBASE"]["apiKey"],
        "authDomain": st.secrets["FIREBASE"]["authDomain"],
        "databaseURL": st.secrets["FIREBASE"]["databaseURL"],
        "projectId": st.secrets["FIREBASE"]["projectId"],
        "storageBucket": st.secrets["FIREBASE"]["storageBucket"],
        "messagingSenderId": st.secrets["FIREBASE"]["messagingSenderId"],
        "appId": st.secrets["FIREBASE"]["appId"]
    }
    return pyrebase.initialize_app(config)

def get_user_role(email):
    import requests
    import streamlit as st

    db_url = st.secrets["FIREBASE"]["databaseURL"]
    encoded_email = email.replace('.', '_').replace('@', '_')

    try:
        res = requests.get(f"{db_url}/users/{encoded_email}/role.json")
        if res.status_code == 200 and res.text != "null":
            return res.json()
        else:
            return "user"
    except Exception as e:
        return "user"
