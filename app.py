import streamlit as st # type: ignore
import os
import json
import pandas as pd
import time
import requests
from urllib.parse import quote
from firebase_helper import init_firebase, get_user_role  # type: ignore
from streamlit_autorefresh import st_autorefresh # type: ignore
from datetime import datetime
from modules.logging import log_admin_action, fetch_admin_logs_csv
from modules.alerts import send_email_alert, retry_failed_emails
from modules.reports import generate_pdf_report

if "current_tab" not in st.session_state:
    st.session_state["current_tab"] = 0

# -------------------------------
# LOGIN
# -------------------------------
import streamlit as st
import os
import requests
from urllib.parse import quote
from firebase_helper import init_firebase, get_user_role

def login_page():
    st.set_page_config(page_title="OCHub Login", layout="centered")

    firebase = init_firebase()
    auth = firebase.auth()

    st.markdown("""
        <style>
            .login-title {
                text-align: center;
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 1.5rem;
                color: #222;
            }
            .login-wrapper {
                max-width: 400px;
                margin: 0 auto;
                padding: 1rem;
            }
            .stTextInput>div>div>input {
                padding: 10px;
                font-size: 14px;
            }
            .stButton>button {
                font-size: 16px;
                padding: 10px;
                width: 100%;
                margin-top: 0.75rem;
            }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)

        if os.path.exists("OCHub_logo.png"):
            st.image("OCHub_logo.png", width=64)

        st.markdown('<div class="login-title">Sign In to OCHub</div>', unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        col1, col2 = st.columns(2)
        with col1:
            login_clicked = st.form_submit_button("Login")
        with col2:
            signup_clicked = st.form_submit_button("Sign Up")

        if login_clicked:
            try:
                user = auth.sign_in_with_email_and_password(email, password)

                # NEW: Check if email is verified
                account_info = auth.get_account_info(user['idToken'])
                is_verified = account_info['users'][0].get('emailVerified', False)
                if not is_verified:
                    st.warning("Please verify your email before logging in. Check your inbox and click the verification link.")
                    return

                role = get_user_role(email)
                st.session_state["role"] = role

                if email == "grich.medor@gmail.com":
                    st.session_state["role"] = "admin"

                # ✅ Check if user is suspended
                encoded_email = quote(email.replace(".", "_"))
                db_url = st.secrets["FIREBASE"]["databaseURL"]
                res = requests.get(f"{db_url}/users/{encoded_email}/status.json")

                if res.status_code == 200 and res.json() == "suspended":
                    st.error("⛔ Your account has been suspended. Please contact the administrator.")
                    return

                # ✅ Proceed if active
                st.session_state["logged_in"] = True
                st.session_state["user_email"] = email
                # FORCE ADMIN -- DO NOT OVERWRITE!
                if email == "grich.medor@gmail.com":
                    st.session_state["role"] = "admin"
                else:
                    st.session_state["role"] = role
                log_admin_action("Login", email)
                st.rerun()

            except Exception as e:
                st.error("Login failed. Check your credentials.")

        if signup_clicked:
            st.session_state["show_register"] = True
            st.session_state["logged_in"] = False
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------
# CREATE ACCOUNT PAGE
# -------------------------------
def create_account_page():
    st.set_page_config(page_title="Create Account | OCHub", layout="centered")

    firebase = init_firebase()
    auth = firebase.auth()

    st.markdown("""
        <style>
        .register-container {
            max-width: 450px;
            margin: auto;
            padding: 0rem;
        }
        .register-title {
            text-align: center;
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 1.5rem;
            color: #222222;
        }
        .stTextInput>div>div>input {
            padding: 10px;
            font-size: 14px;
        }
        .stButton>button {
            font-size: 16px;
            padding: 10px;
            width: 100%;
            margin-top: 0.75rem;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="register-container">', unsafe_allow_html=True)

    if os.path.exists("OCHub_logo.png"):
        st.image("OCHub_logo.png", width=64)

    st.markdown('<div class="register-title">Create Your OCHub Account</div>', unsafe_allow_html=True)

    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    st.markdown(
        '[Terms of Service](https://www.dropbox.com/scl/fi/wz0rol4m28izb3vxh2qnc/terms_of_service.txt?rlkey=634d5p4z2muinmue9t6zc2bqo&st=kerifzdc&dl=0) | [Privacy Policy](https://www.dropbox.com/scl/fi/bsou4pi8vkav76sgpbbm2/privacy_policy.txt?rlkey=buhxuyw22e5r0v86rtukvct5c&st=6pd2fejw&dl=0)'
    )

    agree = st.checkbox("I agree to the Terms of Service and Privacy Policy")

    col1, col2 = st.columns(2)
    with col1:
        register_clicked = st.button("Register")
    with col2:
        back_clicked = st.button("Back to Login")

    if register_clicked:
        if not all([first_name, last_name, email, password, confirm_password]):
            st.error("All fields are required.")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        elif not agree:
            st.error("You must agree to the Terms of Service and Privacy Policy to create an account.")
        else:
            try:
                auth.create_user_with_email_and_password(email, password)
                import requests
                from urllib.parse import quote
                encoded_email = quote(email.replace('.', '_'))
                db_url = st.secrets["FIREBASE"]["databaseURL"]
                user_data = {
                    "role": "user",
                    "status": "active"
                }
                res = requests.put(f"{db_url}/users/{encoded_email}.json", json=user_data)
                user = auth.sign_in_with_email_and_password(email, password)
                auth.send_email_verification(user['idToken'])
                st.info("A verification email has been sent. Please check your inbox and verify your email before logging in.")
                st.success("✅ Account created! Please go log in.")
                st.session_state["show_register"] = False
                st.rerun()
            except Exception as e:
                st.error(f"Registration failed: {e}")

    if back_clicked:
        st.session_state["show_register"] = False
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    
# -------------------------------
# CLASSIFICATION
# -------------------------------
def classify_voltage(v):
    return "🔴 Low" if v < 1.5 else "🟢 Normal" if v <= 3.0 else "🔴 High"
def classify_intensity(i):
    return "🟢 Mild" if i < 4 else "🟡 Moderate" if i <= 8 else "🔴 Critical"
def classify_energy(e):
    return "🟢 Safe" if e < 5 else "🟡 Warning" if e <= 10 else "🔴 Critical"

# -------------------------------
# LOG ALERT TO CSV
# -------------------------------
def log_alert(timestamp, voltage, intensity, energy):
    df = pd.DataFrame([{
        "Timestamp": timestamp,
        "Voltage": voltage,
        "Intensity": intensity,
        "Energy": energy
    }])
    if os.path.exists("alerts_log.csv"):
        df.to_csv("alerts_log.csv", mode='a', header=False, index=False)
    else:
        df.to_csv("alerts_log.csv", index=False)

# -------------------------------
# BACKUP & RESTORE SENSOR SESSION
# -------------------------------

def load_session_data():
    path = "sensor_log.json"
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
                for key in ['voltage_data', 'intensity_data', 'energy_data', 'time_labels', 'activity_log']:
                    st.session_state[key] = data.get(key, [])
        except Exception as e:
            st.warning(f"⚠️ Failed to load session backup: {e}")

def save_session_data():
    path = "sensor_log.json"
    data = {key: st.session_state.get(key, []) for key in
            ['voltage_data', 'intensity_data', 'energy_data', 'time_labels', 'activity_log']}
    try:
        with open(path, "w") as f:
            json.dump(data, f)
    except Exception as e:
        st.warning(f"⚠️ Failed to save session backup: {e}")

# -------------------------------
# DASHBOARD
# -------------------------------
def main_dashboard():
    import os
    import io
    import time
    import random
    import json
    import pandas as pd
    import matplotlib.pyplot as plt
    import requests
    import joblib
    import numpy as np
    from urllib.parse import quote
    from sklearn.linear_model import LinearRegression
    from streamlit_autorefresh import st_autorefresh

    st.set_page_config(page_title="OCHub Dashboard", layout="wide")
    st_autorefresh(interval=5000, key="refresh")
    load_session_data()

    # ✅ Check if name was just updated, and clear the flag
    if st.session_state.get("profile_updated"):
        del st.session_state["profile_updated"]

    # 🔁 Load full name into session at the start of the dashboard
    encoded_email = quote(st.session_state["user_email"].replace(".", "_"))
    profile_url = f"{st.secrets['FIREBASE']['databaseURL']}/users/{encoded_email}/profile.json"
    try:
        res = requests.get(profile_url)
        if res.status_code == 200 and res.json():
            profile = res.json()
            st.session_state["profile_first"] = profile.get("first_name", "")
            st.session_state["profile_last"] = profile.get("last_name", "")
        else:
            st.session_state["profile_first"] = ""
            st.session_state["profile_last"] = ""
    except:
        st.session_state["profile_first"] = ""
        st.session_state["profile_last"] = ""

    # UI Layout
    logo_path = "OCHub_logo.png"
    col1, col2 = st.columns([1, 6])
    with col1:
        if os.path.exists(logo_path):
            st.image(logo_path, width=80)
    with col2:
        st.markdown("## OCHub: Optik-Connect Solutions Hub")

    # Sidebar
    import requests
    from urllib.parse import quote

    st.sidebar.title("👤 User Profile")
    email = st.session_state["user_email"]
    role = st.session_state["role"]

    st.sidebar.write(f"**Email:** {email}")
    st.sidebar.write(f"**Role:** {role.capitalize()}")
    st.sidebar.markdown("---")

    devices = {
        "LED Light (0.1W)": 0.1,
        "Phone (5W)": 5,
        "Laptop (20W)": 20,
        "Fan (50W)": 50
    }
    device = st.sidebar.selectbox("🔌 Select Device", list(devices.keys()))
    st.session_state["selected_device"] = device
    power = devices[device]

    mode = st.sidebar.radio("📡 Data Mode", ["Simulation", "ESP32 Live"], index=0)
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    for key in ['activity_log', 'voltage_data', 'intensity_data', 'energy_data', 'time_labels', 'alerts']:
        st.session_state.setdefault(key, [])

    if mode == "ESP32 Live":
        try:
            with open("sensor_data.json") as f:
                data = json.load(f)
                voltage = float(data["voltage"])
                intensity = float(data["intensity"])
                duration = float(data["duration"])
        except:
            voltage = intensity = duration = 0.0
    else:
        voltage = round(random.uniform(0.5, 3.3), 2)
        intensity = round(random.uniform(1, 10), 1)
        duration = round(random.uniform(0.5, 2.5), 2)

    energy = round(0.5 * intensity * duration, 2)
    time_now = time.strftime("%H:%M:%S")
    seconds = round(energy / power, 1)

    st.session_state['activity_log'].append({
        "Time": time_now,
        "Activity": device.split()[0] + " Output",
        "Voltage (V)": voltage,
        "Intensity": intensity,
        "Energy": energy
    })
    st.session_state['voltage_data'].append(voltage)
    st.session_state['intensity_data'].append(intensity)
    st.session_state['energy_data'].append(energy)
    st.session_state['time_labels'].append(time_now)

    if voltage > 3.0 or intensity > 8 or energy > 10:
        alert = f"⚠️ Alert – V:{voltage}, I:{intensity}, E:{energy} @ {time_now}"
        if not st.session_state['alerts'] or st.session_state['alerts'][-1] != alert:
            st.session_state['alerts'].append(alert)
            st.session_state['unread_alerts'] = True
            log_alert(time_now, voltage, intensity, energy)
            if mode == "ESP32 Live":
                send_email_alert(voltage, intensity, energy, time_now)

    save_session_data()

    tab_names = [
    "📊 Metrics",
    "📈 Charts",
    "📁 Alerts",
    "⚙️ Settings",
    "📡 Live Feed"
]
    selected_tab = st.session_state["current_tab"]
    tabs = st.tabs(tab_names)

    with tabs[0]:
        # Metrics tab content
        st.subheader("📊 Real-Time Sensor Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("🔌 Voltage", f"{voltage} V")
        col2.metric("⚡ Intensity", f"{intensity} A")
        col3.metric("⏱️ Duration", f"{duration} sec")

        power_now = round(voltage * intensity, 2)
        st.session_state.setdefault("total_energy", 0.0)
        st.session_state["total_energy"] += energy

        col4, col5, col6 = st.columns(3)
        col4.metric("⚡ Power", f"{power_now} W")
        col5.metric("🔋 Energy", f"{energy} J")
        col6.metric("📈 Total Energy", f"{round(st.session_state['total_energy'], 2)} J")

        col7, col8, col9 = st.columns(3)
        col7.markdown(classify_voltage(voltage))
        col8.markdown(classify_intensity(intensity))
        col9.markdown(classify_energy(energy))

        st.markdown("### 🤖 Predicted Activity Type")
        try:
            input_df = pd.DataFrame([[intensity, duration]], columns=["intensity", "duration"])
            model = joblib.load("activity_classifier_model_mac.pkl")
            prediction = model.predict(input_df)[0]

            if hasattr(model, "predict_proba"):
                prob = model.predict_proba(input_df).max()
                st.session_state["detected_activity"] = prediction.upper()
                st.session_state["activity_confidence"] = round(prob * 100, 1)
                st.markdown(f"<span style='color: green; font-weight: bold;'>AI Detected Activity: {prediction.upper()} ({round(prob * 100, 1)}% confidence)</span>", unsafe_allow_html=True)
            else:
                st.session_state["detected_activity"] = prediction.upper()
                st.session_state["activity_confidence"] = 0.0
                st.markdown(f"<span style='color: green; font-weight: bold;'>AI Detected Activity: {prediction.upper()}</span>", unsafe_allow_html=True)

        except Exception as e:
            st.warning(f"⚠️ Could not load or use AI model: {e}")

        st.markdown(f"### ⏳ Estimated Runtime for {device}")
        st.write(f"⏱️ Usage time: **{seconds} sec**")

        st.markdown("### 🔌 Live Device Energy Impact Estimator")
        impact_data = {
            "LED Light (0.1W)": round(energy / 0.1, 2),
            "Phone (5W)": round(energy / 5, 2),
            "Laptop (20W)": round(energy / 20, 2),
            "Fan (50W)": round(energy / 50, 2)
        }
        impact_df = pd.DataFrame({
            "Device": list(impact_data.keys()),
            "Runtime (sec)": list(impact_data.values())
        })
        st.bar_chart(impact_df.set_index("Device"))

        st.markdown("### 📈 Trend Analysis + Smart Suggestions")
        def detect_trend(data):
            if len(data) < 5:
                return "🟡 Not enough data for trend"
            y = np.array(data[-5:]).reshape(-1, 1)
            x = np.array(range(len(y))).reshape(-1, 1)
            model = LinearRegression().fit(x, y)
            slope = model.coef_[0][0]
            if slope > 0.05:
                return "🔼 Rising"
            elif slope < -0.05:
                return "🔽 Falling"
            else:
                return "⚖️ Stable"

        voltage_trend = detect_trend(st.session_state["voltage_data"])
        intensity_trend = detect_trend(st.session_state["intensity_data"])
        energy_trend = detect_trend(st.session_state["energy_data"])

        st.write(f"**Voltage Trend:** {voltage_trend}")
        st.write(f"**Intensity Trend:** {intensity_trend}")
        st.write(f"**Energy Trend:** {energy_trend}")

        st.markdown("### 🧠 AI Suggestion")
        suggestion = "✅ System stable. Energy capture consistent."
        if "🔼" in energy_trend and intensity > 8:
            suggestion = "⚠️ High motion detected. Monitor intensity levels."
        elif "🔽" in energy_trend and intensity < 3:
            suggestion = "ℹ️ Motion decreasing. Consider repositioning sensor."
        elif "🔼" in voltage_trend and voltage > 3.5:
            suggestion = "⚡ Voltage rising rapidly — check potential spike source."
        st.info(suggestion)

        st.markdown("### 🎯 Live Gauge Meters")
        def draw_gauge(value, label, min_val, max_val, warning_range, critical_range):
            fig, ax = plt.subplots(figsize=(2.5, 1.5))
            ax.axis('off')
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 1)
            color = "green"
            if value >= critical_range:
                color = "red"
            elif value >= warning_range:
                color = "orange"
            ax.barh(0.5, min(value, max_val), height=0.3, left=0, color=color)
            ax.text(5, 0.9, f"{label}: {value}", ha='center', fontsize=10, fontweight='bold')
            ax.plot([warning_range, warning_range], [0.2, 0.8], "k--", linewidth=1)
            ax.plot([critical_range, critical_range], [0.2, 0.8], "k--", linewidth=1)
            plt.close(fig)
            return fig

        g1, g2, g3 = st.columns(3)
        with g1:
            st.pyplot(draw_gauge(voltage, "Voltage (V)", 0, 4.2,
                                 st.session_state.get("voltage_threshold", 3.0),
                                 st.session_state.get("voltage_threshold", 3.0) + 0.5))
        with g2:
            st.pyplot(draw_gauge(intensity, "Intensity (A)", 0, 20,
                                 st.session_state.get("intensity_threshold", 8.0),
                                 st.session_state.get("intensity_threshold", 8.0) + 2.0))
        with g3:
            st.pyplot(draw_gauge(energy, "Energy (J)", 0, 50,
                                 st.session_state.get("energy_threshold", 10.0),
                                 st.session_state.get("energy_threshold", 10.0) + 5.0))

        st.markdown("### 📊 Activity Log")
        for entry in reversed(st.session_state['activity_log'][-10:]):
            st.write(f"{entry['Time']} - {entry['Activity']} ({entry['Voltage (V)']}V, {entry['Intensity']}A)")

        st.download_button("⬇️ Download Log",
            data=pd.DataFrame(st.session_state['activity_log']).to_csv(index=False),
            file_name="ochub_activity_log.csv", mime='text/csv')

        st.markdown("### 📁 Export Dashboard Data")
        try:
            df = pd.DataFrame({
                "Voltage": st.session_state['voltage_data'],
                "Intensity": st.session_state['intensity_data'],
                "Energy": st.session_state['energy_data']
            }, index=st.session_state['time_labels'])

            df = df.dropna().iloc[::5].rolling(window=10).mean()

            fig, ax = plt.subplots(figsize=(10, 4))
            df.plot(ax=ax)
            ax.set_title("Smoothed Voltage, Intensity & Energy Over Time")
            ax.set_ylabel("Sensor Value")
            ax.set_xlabel("Time")
            ax.grid(True)
            plt.xticks(rotation=30)

            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plt.close(fig)

            st.download_button("⬇️ Download Chart (PNG)", data=buf,
                               file_name="ochub_chart.png", mime="image/png")
        except Exception as e:
            st.warning(f"⚠️ Could not generate chart: {e}")

        st.markdown("### 📄 Export Full Report (PDF)")
        pdf_file = generate_pdf_report()
        st.download_button("⬇️ Download PDF Report", data=pdf_file,
                           file_name="OCHub_Energy_Report.pdf", mime="application/pdf")

    with tabs[1]:
        # Charts tab content
        st.subheader("📈 Historical Sensor Charts")
        try:
            df = pd.DataFrame({
                "Voltage": st.session_state["voltage_data"],
                "Intensity": st.session_state["intensity_data"],
                "Energy": st.session_state["energy_data"]
            }, index=st.session_state["time_labels"])
            df.dropna(inplace=True)
            if df.empty or df.shape[0] < 10:
                st.warning("📉 Not enough data to display the chart.")
            else:
                df = df.iloc[::5].rolling(window=10).mean()
                fig, ax = plt.subplots(figsize=(10, 4))
                df.plot(ax=ax)
                ax.set_title("Smoothed Voltage, Intensity & Energy Over Time")
                ax.set_ylabel("Sensor Value")
                ax.set_xlabel("Time")
                ax.grid(True)
                plt.xticks(rotation=45)
                st.pyplot(fig)
        except Exception as e:
            st.error(f"⚠️ Failed to render chart: {e}")

    with tabs[2]:
        # Alerts tab content
        if st.session_state["role"] == "admin":
            st.session_state["unread_alerts"] = False

            st.subheader("📁 Real-Time Alert Feed")

            # Show last email error if it exists
            if "last_email_error" in st.session_state:
                st.error(st.session_state["last_email_error"])

            # Show alerts if any exist
            if st.session_state.get("alerts"):
                for alert in reversed(st.session_state["alerts"][-10:]):
                    if "⚠️" in alert:
                        st.warning(alert)
                    else:
                        st.info(alert)

                if os.path.exists("alerts_log.csv"):
                    with open("alerts_log.csv", "rb") as f:
                        st.download_button(
                            label="⬇️ Download Alerts Log",
                            data=f,
                            file_name="alerts_log.csv",
                            mime="text/csv"
                        )
            else:
                st.success("✅ No alerts triggered yet.")

            st.markdown("### 🔁 Retry Failed Email Alerts")
            if st.button("🔄 Retry Now"):
                retry_result = retry_failed_emails()
                st.info(retry_result)

        else:
            st.warning("⛔ Access restricted to Admins.")


    with tabs[3]:
        # Settings tab content
        if st.session_state["role"] == "admin":
            st.subheader("⚙️ Settings")

            # Auto-refresh toggle
            auto = st.checkbox("🔄 Auto-Refresh", value=st.session_state.get("auto_refresh_enabled", True))
            st.session_state["auto_refresh_enabled"] = auto

            # Dark mode toggle
            dark = st.checkbox("🌙 Dark Mode", value=st.session_state.get("dark_mode", False))
            st.session_state["dark_mode"] = dark

            if dark:
                st.markdown("""
                    <style>
                        body { background-color: #111111; color: white; }
                        .stApp { background-color: #111111; }
                    </style>
                """, unsafe_allow_html=True)

            # Alert thresholds
            st.markdown("### 🛡️ Alert Thresholds")

            voltage_thresh = st.slider("🔌 Voltage Threshold (V)", 0.5, 4.2, step=0.1,
                                       value=st.session_state.get("voltage_threshold", 3.0))
            intensity_thresh = st.slider("⚡ Intensity Threshold (A)", 0.5, 20.0, step=0.5,
                                         value=st.session_state.get("intensity_threshold", 8.0))
            energy_thresh = st.slider("🔋 Energy Threshold (J)", 0.5, 50.0, step=0.5,
                                      value=st.session_state.get("energy_threshold", 10.0))

            if st.button("💾 Save Settings"):
                st.session_state["voltage_threshold"] = voltage_thresh
                st.session_state["intensity_threshold"] = intensity_thresh
                st.session_state["energy_threshold"] = energy_thresh
                st.success("✅ Thresholds saved successfully.")

        else:
            st.warning("⛔ Settings are only available to Admins.")

    with tabs[4]:
        # Live Feed tab content
        st.subheader("📡 Live ESP32 Sensor Feed")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Voltage (V)", f"{voltage}")
        col2.metric("Intensity (A)", f"{intensity}")
        col3.metric("Duration (s)", f"{duration}")
        col4.metric("Energy (J)", f"{energy}")

        # Sensor file status
        sensor_path = "sensor_data.json"

        try:
            sensor_mtime = os.path.getmtime(sensor_path)
            last_update = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(sensor_mtime))
            time_diff = round(time.time() - sensor_mtime, 1)

            if time_diff > 10:
                st.error("📶 Sensor Status: 🔴 Offline")
            else:
                st.success(f"📶 Sensor Status: 🟢 Online\n⏱️ Last Update: {last_update} ({time_diff} sec ago)")
        except Exception as e:
            st.warning(f"📶 Sensor Status: ⚠️ Unknown — {e}")

# -------------------------------
# ENTRY POINT (PAGE CONTROLLER)
# -------------------------------

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "show_register" not in st.session_state:
    st.session_state["show_register"] = False

if st.session_state["logged_in"]:
    main_dashboard()
elif st.session_state["show_register"]:
    create_account_page()
else:
    login_page()
