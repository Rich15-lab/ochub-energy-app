import io
import os
import time
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .charts import generate_chart_image_file, generate_gauge_chart_image


def detect_trend(data):
    if len(data) < 5:
        return "Not enough data"
    import pandas as pd
    y = pd.Series(data[-5:])
    slope = y.diff().mean()
    if slope > 0.05:
        return "Rising"
    elif slope < -0.05:
        return "Falling"
    else:
        return "Stable"


def generate_pdf_report():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    now = time.strftime('%Y-%m-%d %H:%M:%S')

    # Extract values from session
    v = st.session_state["voltage_data"][-1]
    i = st.session_state["intensity_data"][-1]
    e = st.session_state["energy_data"][-1]
    total_energy = round(st.session_state.get("total_energy", 0), 2)
    time_labels = st.session_state["time_labels"]

    # Save charts
    chart_path = generate_chart_image_file(
        st.session_state["voltage_data"],
        st.session_state["intensity_data"],
        st.session_state["energy_data"],
        time_labels
    )
    gauge_path = generate_gauge_chart_image(v, i, e)

    # Status checks
    def classify_voltage(v): return "Low" if v < 1.5 else "Normal" if v <= 3.0 else "High"
    def classify_intensity(i): return "Mild" if i < 4 else "Moderate" if i <= 8 else "Critical"
    def classify_energy(e): return "Safe" if e < 5 else "Warning" if e <= 10 else "Critical"

    suggestion = "System stable. Energy capture consistent."
    if i > 8:
        suggestion = "High motion detected. Monitor intensity levels."
    elif i < 3:
        suggestion = "Motion decreasing. Consider repositioning sensor."
    elif v > 3.5:
        suggestion = "Voltage rising rapidly — check potential spike source."

    voltage_trend = detect_trend(st.session_state["voltage_data"])
    intensity_trend = detect_trend(st.session_state["intensity_data"])
    energy_trend = detect_trend(st.session_state["energy_data"])

    prediction = st.session_state.get("detected_activity", "Unknown")
    confidence = st.session_state.get("activity_confidence", 0.0)
    selected_device = st.session_state.get("selected_device", "Phone (5W)")
    devices = {
        "LED Light (0.1W)": 0.1,
        "Phone (5W)": 5.0,
        "Laptop (20W)": 20.0,
        "Fan (50W)": 50.0
    }
    device_power = devices.get(selected_device, 5.0)
    estimated_runtime = round(e / device_power, 2)

    try:
        sensor_path = "sensor_data.json"
        sensor_mtime = os.path.getmtime(sensor_path)
        sensor_last_updated = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(sensor_mtime))
        time_diff_sec = round(time.time() - sensor_mtime, 1)
        sensor_status = "ONLINE" if time_diff_sec < 10 else "OFFLINE"
    except:
        sensor_status = "UNKNOWN"
        sensor_last_updated = "N/A"
        time_diff_sec = "N/A"

    # Page 1 – Summary
    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "OCHub: Energy Metrics Report")
    y -= 20
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Report Generated: {now}")

    y -= 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Live Metrics Summary")
    y -= 20
    c.setFont("Helvetica", 11)
    for line in [
        f"Voltage: {v:.2f} V", f"Intensity: {i:.2f} A", f"Energy: {e:.2f} J",
        f"Total Energy: {total_energy:.2f} J", f"Voltage Status: {classify_voltage(v)}",
        f"Intensity Status: {classify_intensity(i)}", f"Energy Status: {classify_energy(e)}"
    ]:
        c.drawString(50, y, line)
        y -= 15

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "AI Activity Detection")
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Predicted Activity: {prediction}")
    y -= 15
    c.drawString(50, y, f"Confidence: {confidence}%")

    y -= 25
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Device Runtime Estimation")
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Selected Device: {selected_device}")
    y -= 15
    c.drawString(50, y, f"Estimated Runtime: {estimated_runtime} sec")

    y -= 25
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "System Health")
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"ESP32 Sensor Status: {sensor_status}")
    y -= 15
    c.drawString(50, y, f"Last Update: {sensor_last_updated}")
    y -= 15
    c.drawString(50, y, f"Delay: {time_diff_sec} seconds")

    y -= 25
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "AI Suggestion")
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(50, y, suggestion)

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Trend Analysis")
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Voltage Trend: {voltage_trend}")
    y -= 15
    c.drawString(50, y, f"Intensity Trend: {intensity_trend}")
    y -= 15
    c.drawString(50, y, f"Energy Trend: {energy_trend}")

    c.showPage()

    # Page 2 – Charts
    y = height - 50
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Sensor Chart Overview")
    y -= 210
    c.drawImage(chart_path, 50, y, width=500, height=200)

    y -= 230
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Live Gauge Summary")
    y -= 210
    c.drawImage(gauge_path, 50, y, width=500, height=200)

    # Page 3 – Activity Log
    c.showPage()
    y = height - 50
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Recent Activity Log")
    c.setFont("Helvetica", 10)
    y -= 20
    for entry in reversed(st.session_state["activity_log"][-10:]):
        log_line = f"{entry['Time']} - {entry['Activity']} (V: {entry['Voltage (V)']} | I: {entry['Intensity']} | E: {entry['Energy']})"
        c.drawString(50, y, log_line)
        y -= 15

    c.save()
    buffer.seek(0)
    return buffer
