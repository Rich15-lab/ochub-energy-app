import os
import pandas as pd
import smtplib
import io
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
from datetime import datetime


def send_email_alert(voltage, intensity, energy, timestamp):
    sender = st.secrets["EMAIL"]["EMAIL_FROM"]
    password = st.secrets["EMAIL"]["EMAIL_PASSWORD"]
    receiver = st.secrets["EMAIL"]["EMAIL_TO"]

    subject = "⚠️ OCHub Critical Alert"
    body = f"""A critical alert was triggered at {timestamp}:

Voltage: {voltage} V
Intensity: {intensity}
Energy: {energy} J

Please take immediate action if necessary."""

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        print("✅ Email alert sent.")
        return True
    except Exception as e:
        print(f"❌ Email failed: {e}")
        st.session_state["last_email_error"] = str(e)

        # Backup log
        failed_log = pd.DataFrame([{
            "Timestamp": timestamp,
            "Voltage": voltage,
            "Intensity": intensity,
            "Energy": energy,
            "Error": str(e)
        }])
        if os.path.exists("failed_email_log.csv"):
            failed_log.to_csv("failed_email_log.csv", mode='a', header=False, index=False)
        else:
            failed_log.to_csv("failed_email_log.csv", index=False)
        return False


def retry_failed_emails():
    failed_log_path = "failed_email_log.csv"
    if not os.path.exists(failed_log_path):
        return "✅ No failed emails to retry."

    df_failed = pd.read_csv(failed_log_path)
    if df_failed.empty:
        return "✅ No failed emails to retry."

    remaining_errors = []

    for _, row in df_failed.iterrows():
        success = send_email_alert(
            voltage=row["Voltage"],
            intensity=row["Intensity"],
            energy=row["Energy"],
            timestamp=row["Timestamp"]
        )
        if not success:
            remaining_errors.append(row)

    if remaining_errors:
        pd.DataFrame(remaining_errors).to_csv(failed_log_path, index=False)
        return f"⚠️ Retried. {len(remaining_errors)} emails still failed."
    else:
        os.remove(failed_log_path)
        return "✅ All failed emails resent successfully."
