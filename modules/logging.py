import requests
import random
from urllib.parse import quote
from datetime import datetime
import streamlit as st


def log_admin_action(action, who_did_it, who_it_happened_to=""):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log = {
            "time": timestamp,
            "action": action,
            "by": who_did_it,
            "target": who_it_happened_to
        }

        db_url = st.secrets["FIREBASE"]["databaseURL"]
        key = quote(f"{timestamp.replace(' ', '_').replace(':', '-')}_{random.randint(1000, 9999)}")
        url = f"{db_url}/logs/{key}.json"

        print("🔥 LOG PUT URL:", url)
        print("🔥 LOG DATA:", log)

        requests.put(url, json=log)

    except Exception as e:
        st.warning(f"⚠️ Could not save log: {e}")


def fetch_admin_logs_csv():
    try:
        db_url = st.secrets["FIREBASE"]["databaseURL"]
        res = requests.get(f"{db_url}/logs.json")

        if res.status_code == 200 and res.json():
            logs = res.json()
            records = []

            for entry in logs.values():
                records.append({
                    "Time": entry.get("time", ""),
                    "Action": entry.get("action", ""),
                    "By": entry.get("by", ""),
                    "Target": entry.get("target", "")
                })

            import pandas as pd
            return pd.DataFrame(records)
        else:
            return pd.DataFrame()

    except Exception as e:
        st.error(f"❌ Could not fetch admin logs: {e}")
        return pd.DataFrame()
