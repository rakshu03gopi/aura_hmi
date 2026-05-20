import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from collections import deque
import time
import requests
import json


# =========================================================
# AURA HMI v3.0
# AI-Driven Next Generation Industrial HMI
# Powered by Groq AI (Free)
# =========================================================

st.set_page_config(
    page_title="AURA HMI v3.0",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.stApp {
    background-color: #0b0e14;
    color: white;
}

section[data-testid="stSidebar"] {
    background-color: #111827;
    border-right: 1px solid #1f2937;
}

[data-testid="stMetricValue"] {
    font-size: 34px;
    color: #00f2ff;
    font-weight: 700;
}

[data-testid="stMetricLabel"] {
    color: #9ca3af;
}

.stButton > button {
    width: 100%;
    border-radius: 10px;
    height: 3.3em;
    background-color: #1f2937;
    color: white;
    border: 1px solid #374151;
    transition: 0.3s;
}

.stButton > button:hover {
    border-color: #3b82f6;
    background-color: #2563eb;
}

.alarm-card {
    background-color: #111827;
    padding: 15px;
    border-radius: 12px;
    border-left: 6px solid red;
    margin-bottom: 10px;
}

.success-card {
    background-color: #111827;
    padding: 15px;
    border-radius: 12px;
    border-left: 6px solid #10b981;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================

if "system_state" not in st.session_state:
    st.session_state.system_state = "OPERATIONAL"

if "logs" not in st.session_state:
    st.session_state.logs = ["System Initialized"]

if "cycle" not in st.session_state:
    st.session_state.cycle = 0

if "failure_mode" not in st.session_state:
    st.session_state.failure_mode = False

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "alarm_feed" not in st.session_state:
    st.session_state.alarm_feed = []

if "sensor_history" not in st.session_state:
    st.session_state.sensor_history = {
        "temperature": deque(maxlen=100),
        "vibration": deque(maxlen=100),
        "current": deque(maxlen=100),
        "pressure": deque(maxlen=100)
    }

if "groq_ready" not in st.session_state:
    st.session_state.groq_ready = False

if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = ""

# =========================================================
# THRESHOLDS
# =========================================================

THRESHOLDS = {
    "temperature": {"warning": 80, "critical": 100},
    "vibration": {"warning": 0.5, "critical": 0.8},
    "current": {"warning": 6, "critical": 8},
    "pressure": {"warning": 120, "critical": 140}
}

# =========================================================
# LOGGING
# =========================================================

def add_log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, f"[{timestamp}] {message}")

# =========================================================
# SENSOR ENGINE
# =========================================================

def generate_sensor_data():

    st.session_state.cycle += 1
    c = st.session_state.cycle

    if c > 20:
        st.session_state.failure_mode = True

    if st.session_state.failure_mode:

        ramp = min((c - 20) * 2, 45)

        readings = {
            "temperature": round(70 + ramp + np.random.uniform(-2, 2), 2),
            "vibration": round(0.25 + ramp * 0.02 + np.random.uniform(-0.02, 0.02), 3),
            "current": round(4.5 + ramp * 0.14 + np.random.uniform(-0.1, 0.1), 2),
            "pressure": round(108 + ramp * 0.9 + np.random.uniform(-1, 1), 2),
        }

    else:

        readings = {
            "temperature": round(np.random.uniform(60, 72), 2),
            "vibration": round(np.random.uniform(0.1, 0.3), 3),
            "current": round(np.random.uniform(4.0, 5.0), 2),
            "pressure": round(np.random.uniform(100, 112), 2),
        }

    for k, v in readings.items():
        st.session_state.sensor_history[k].append(v)

    return readings

# =========================================================
# AI PRIORITIZER
# =========================================================

def alarm_priority(sensor, value):

    t = THRESHOLDS[sensor]

    if value >= t["critical"]:
        severity = 3
    elif value >= t["warning"]:
        severity = 2
    else:
        severity = 1

    history = list(st.session_state.sensor_history[sensor])

    frequency = sum(
        1 for v in history if v >= t["warning"]
    ) / max(len(history), 1)

    criticality = {
        "temperature": 1.0,
        "vibration": 0.9,
        "current": 0.8,
        "pressure": 0.7
    }[sensor]

    score = (severity * 0.5) + (frequency * 0.3) + (criticality * 0.2)

    return round(score, 2)

# =========================================================
# ROOT CAUSE ENGINE
# =========================================================

def root_cause_analysis(readings):

    critical = []

    for sensor, value in readings.items():
        if value >= THRESHOLDS[sensor]["critical"]:
            critical.append(sensor)

    if "temperature" in critical and "vibration" in critical:
        return {
            "root_cause": "Motor Bearing Failure",
            "severity": "CRITICAL",
            "recommendation": "Immediate shutdown recommended"
        }

    elif "temperature" in critical and "current" in critical:
        return {
            "root_cause": "Electrical Overload",
            "severity": "CRITICAL",
            "recommendation": "Reduce load and inspect wiring"
        }

    elif "pressure" in critical:
        return {
            "root_cause": "Pressure System Anomaly",
            "severity": "CRITICAL",
            "recommendation": "Check pressure release valve"
        }

    return None

# =========================================================
# PREDICTIVE FAILURE ENGINE
# =========================================================

def time_to_failure(sensor):

    history = list(st.session_state.sensor_history[sensor])

    if len(history) < 10:
        return None

    recent = history[-10:]
    rate = (recent[-1] - recent[0]) / 10

    if rate <= 0:
        return None

    threshold = THRESHOLDS[sensor]["critical"]
    current = recent[-1]

    if current >= threshold:
        return 0

    return int((threshold - current) / rate)

# =========================================================
# GROQ AI CHATBOT
# =========================================================

def call_groq_api(prompt, api_key):
    """Call Groq API via requests — 100% free tier."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": "You are AURA, an intelligent AI assistant for an industrial HMI system. Be concise, direct, and practical. Always give specific numbers and actions."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 512,
        "temperature": 0.3
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            err = response.json()
            return f"API Error {response.status_code}: {err.get('error', {}).get('message', 'Unknown error')}"

    except requests.exceptions.Timeout:
        return "Request timed out. Please try again."
    except Exception as e:
        return f"Connection error: {str(e)}"


def test_groq_connection(api_key):
    """Test if the Groq API key works."""
    result = call_groq_api("Reply with: AURA ONLINE", api_key)
    return "API Error" not in result and "Connection error" not in result and "timed out" not in result


def chatbot_groq(question, readings, root, api_key):
    """Groq-powered chatbot with full plant context."""

    ttf_info = {}
    for s in readings:
        ttf = time_to_failure(s)
        if ttf is not None:
            ttf_info[s] = f"{ttf} seconds"

    prompt = f"""=== CURRENT PLANT DATA ===
Sensor Readings:
- Temperature: {readings['temperature']} degrees C  (Warning: 80, Critical: 100)
- Vibration: {readings['vibration']} mm/s            (Warning: 0.5, Critical: 0.8)
- Current: {readings['current']} A                   (Warning: 6A, Critical: 8A)
- Pressure: {readings['pressure']} PSI               (Warning: 120, Critical: 140)

System State: {st.session_state.system_state}
Failure Mode Active: {st.session_state.failure_mode}
Runtime Cycle: {st.session_state.cycle}

Root Cause Detected: {root if root else "None - all systems normal"}

Estimated Time to Failure:
{ttf_info if ttf_info else "No imminent failures predicted"}

Recent Logs:
{chr(10).join(st.session_state.logs[:5])}

=== INSTRUCTIONS ===
- Answer in clear, concise language for an industrial operator
- Give specific numbers and actions, not vague answers
- If there is a critical issue, always mention it
- Keep answers under 4 sentences unless detail is needed

Operator Question: {question}"""

    return call_groq_api(prompt, api_key)


def chatbot_fallback(question, readings, root):
    """Fallback keyword chatbot when Groq is not connected."""
    q = question.lower()

    if "status" in q or "problem" in q or "wrong" in q or "happening" in q:
        if root:
            return f"Critical Issue: {root['root_cause']}. {root['recommendation']}"
        return "All systems operating normally."

    elif "temperature" in q or "temp" in q or "heat" in q:
        val = readings['temperature']
        status = "CRITICAL" if val >= 100 else "WARNING" if val >= 80 else "NORMAL"
        return f"Temperature is {val} degrees C - {status}. Critical threshold is 100."

    elif "pressure" in q:
        val = readings['pressure']
        status = "CRITICAL" if val >= 140 else "WARNING" if val >= 120 else "NORMAL"
        return f"Pressure is {val} PSI - {status}. Critical threshold is 140 PSI."

    elif "vibration" in q or "vib" in q:
        val = readings['vibration']
        status = "CRITICAL" if val >= 0.8 else "WARNING" if val >= 0.5 else "NORMAL"
        return f"Vibration is {val} mm/s - {status}. Critical threshold is 0.8."

    elif "current" in q or "power" in q or "electric" in q:
        val = readings['current']
        status = "CRITICAL" if val >= 8 else "WARNING" if val >= 6 else "NORMAL"
        return f"Current is {val}A - {status}. Critical threshold is 8A."

    elif "failure" in q or "fail" in q or "time" in q or "predict" in q:
        outputs = []
        for s in readings:
            ttf = time_to_failure(s)
            if ttf is not None:
                outputs.append(f"{s}: {ttf}s")
        if outputs:
            return "Estimated time to failure - " + ", ".join(outputs)
        return "No imminent failures predicted based on current trends."

    elif "shutdown" in q or "stop" in q:
        if root and root["severity"] == "CRITICAL":
            return f"Yes - immediate shutdown recommended. Reason: {root['root_cause']}."
        return "No shutdown required. System is within safe operating parameters."

    elif "safe" in q or "normal" in q or "ok" in q:
        if root:
            return f"System is NOT safe. {root['root_cause']} detected. {root['recommendation']}."
        return "System is operating safely. All sensors within normal range."

    elif "zone" in q:
        if root:
            return "Zone D is showing critical readings. Motor bearing stress detected in that sector."
        return "All zones operating normally. No anomalies detected."

    elif "recommend" in q or "advice" in q or "should" in q:
        if root:
            return f"Recommended action: {root['recommendation']}. Priority: {root['severity']}."
        return "No action needed. Continue monitoring."

    return "Connect Groq AI above for full natural language support. Or ask about: temperature, pressure, vibration, current, status, failure prediction, zones, or shutdown."


def chatbot(question, readings, root):
    """Main chatbot router."""
    if st.session_state.groq_ready and st.session_state.groq_api_key:
        return chatbot_groq(question, readings, root, st.session_state.groq_api_key)
    else:
        return chatbot_fallback(question, readings, root)

# =========================================================
# LIVE DATA
# =========================================================

readings = generate_sensor_data()
root = root_cause_analysis(readings)

# =========================================================
# AUTO ALARM FEED
# =========================================================

if root:
    st.session_state.alarm_feed.insert(0, {
        "time": datetime.now().strftime("%H:%M:%S"),
        "message": root["root_cause"],
        "recommendation": root["recommendation"]
    })

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title("AURA HMI")

    role = st.selectbox(
        "ROLE MODE",
        ["Operator", "Engineer", "Manager"]
    )

    if role == "Operator":
        available_views = ["Plant Overview", "AI Alarm Center", "Emergency", "AI Chat"]
    elif role == "Engineer":
        available_views = ["Plant Overview", "AI Alarm Center", "Maintenance", "Emergency", "No-Code Builder", "AI Chat"]
    else:
        available_views = ["Plant Overview", "AI Chat"]

    view = st.radio("DASHBOARD", available_views)

    st.divider()

    st.write("### System State")
    if st.session_state.system_state == "OPERATIONAL":
        st.success(st.session_state.system_state)
    else:
        st.error(st.session_state.system_state)

    st.write("### Runtime Cycle")
    st.info(st.session_state.cycle)

    if st.button("⚡ Trigger Failure"):
        st.session_state.failure_mode = True
        add_log("Manual failure mode triggered")

    if st.button("✅ Reset System"):
        st.session_state.failure_mode = False
        st.session_state.cycle = 0
        st.session_state.system_state = "OPERATIONAL"
        for k in st.session_state.sensor_history:
            st.session_state.sensor_history[k].clear()
        add_log("System reset")

    st.divider()

    if st.session_state.groq_ready:
        st.success("🤖 Groq AI: Online")
    else:
        st.warning("🤖 Groq AI: Offline")

    st.write("### Recent Logs")
    for log in st.session_state.logs[:6]:
        st.caption(log)

# =========================================================
# PLANT OVERVIEW
# =========================================================

if view == "Plant Overview":

    st.title("🗺️ Smart Plant Overview")

    health = 100
    if root:
        health = 62

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Plant Health", f"{health}%")
    c2.metric("Temperature", f"{readings['temperature']} °C")
    c3.metric("Pressure", f"{readings['pressure']} PSI")
    c4.metric("Power Usage", f"{round(readings['current']*20,1)} kW")

    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Plant Layout")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[1, 2, 3, 4],
            y=[4, 3, 2, 1],
            mode='markers+text',
            marker=dict(
                size=[50, 60, 50, 70],
                color=[
                    "green",
                    "orange",
                    "green",
                    "red" if root else "green"
                ]
            ),
            text=["Zone A", "Zone B", "Zone C", "Zone D"],
            textposition="bottom center"
        ))
        fig.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("AI Insights")
        if root:
            st.error(f"🚨 {root['root_cause']}")
            st.warning(root["recommendation"])
            for sensor in readings:
                ttf = time_to_failure(sensor)
                if ttf is not None and ttf < 120:
                    st.error(f"⏱️ {sensor.upper()} fails in {ttf}s")
        else:
            st.success("Plant operating normally")

# =========================================================
# AI ALARM CENTER
# =========================================================

elif view == "AI Alarm Center":

    st.title("🚨 AI Alarm Feed")

    priorities = []
    for sensor, value in readings.items():
        score = alarm_priority(sensor, value)
        priorities.append((sensor, value, score))

    priorities = sorted(priorities, key=lambda x: x[2], reverse=True)

    for sensor, value, score in priorities:

        status = "NORMAL"
        if value >= THRESHOLDS[sensor]["critical"]:
            status = "CRITICAL"
        elif value >= THRESHOLDS[sensor]["warning"]:
            status = "WARNING"

        color = "🔴" if status == "CRITICAL" else "🟡" if status == "WARNING" else "🟢"

        st.markdown(f"""
        <div class="alarm-card">
        <h4>{color} {sensor.upper()}</h4>
        <p>Value: <b>{value}</b></p>
        <p>AI Priority Score: <b>{score}</b></p>
        <p>Status: <b>{status}</b></p>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.button(f"Acknowledge {sensor}", key=f"ack_{sensor}")
        with c2:
            st.button(f"Snooze {sensor}", key=f"snz_{sensor}")
        with c3:
            st.button(f"Escalate {sensor}", key=f"esc_{sensor}")

    if root:
        st.markdown("---")
        st.subheader("🧠 AI Root Cause Summary")
        st.error(f"**{root['root_cause']}** — {root['recommendation']}")

# =========================================================
# MAINTENANCE VIEW
# =========================================================

elif view == "Maintenance":

    st.title("🔧 Predictive Maintenance Dashboard")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperature", readings["temperature"])
    c2.metric("Vibration", readings["vibration"])
    c3.metric("Current", readings["current"])
    c4.metric("Pressure", readings["pressure"])

    st.markdown("---")

    any_ttf = False
    for sensor in readings:
        ttf = time_to_failure(sensor)
        if ttf is not None and ttf < 120:
            st.warning(f"⏱️ {sensor.upper()} predicted failure in **{ttf} seconds**")
            any_ttf = True
    if not any_ttf:
        st.success("No imminent failures predicted")

    st.subheader("AI Priority Scores")
    score_cols = st.columns(4)
    for i, (sensor, value) in enumerate(readings.items()):
        score = alarm_priority(sensor, value)
        icon = "🔴" if score > 2.0 else "🟡" if score > 1.2 else "🟢"
        score_cols[i].metric(f"{icon} {sensor.capitalize()}", f"{value}", f"Score: {score}")

    temp_hist = list(st.session_state.sensor_history["temperature"])
    vib_hist = list(st.session_state.sensor_history["vibration"])
    length = min(len(temp_hist), 50)

    df = pd.DataFrame({
        "Time": range(length),
        "Temperature": temp_hist[-length:],
        "Vibration": vib_hist[-length:]
    })

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Time"], y=df["Temperature"], name="Temperature", line=dict(color="#ef4444", width=2)))
    fig.add_trace(go.Scatter(x=df["Time"], y=df["Vibration"], name="Vibration", line=dict(color="#00f2ff", width=2)))
    fig.update_layout(template="plotly_dark", height=500, title="Live Sensor Trends")
    st.plotly_chart(fig, use_container_width=True)

# =========================================================
# EMERGENCY VIEW
# =========================================================

elif view == "Emergency":

    st.title("🚨 Emergency Command Center")

    c1, c2 = st.columns([1, 1])

    with c1:
        if root:
            st.error(f"**{root['root_cause']}**")
            st.warning(root["recommendation"])
            for sensor in readings:
                ttf = time_to_failure(sensor)
                if ttf is not None and ttf < 60:
                    st.error(f"⏱️ {sensor.upper()} CRITICAL — {ttf}s to failure")
        else:
            st.success("No emergency detected")

        st.markdown("---")

        if st.button("🔴 EMERGENCY SHUTDOWN"):
            st.session_state.system_state = "SHUTDOWN"
            add_log("Emergency shutdown activated")
            st.rerun()

        if st.button("🌀 Activate Fire Suppression"):
            add_log("Fire suppression system activated")
            st.toast("Fire suppression activated!", icon="🌀")

        if st.button("📢 Alert Maintenance Team"):
            add_log("Maintenance team alerted")
            st.toast("Maintenance team notified!", icon="📢")

    with c2:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=readings["temperature"],
            title={"text": "Critical Heat Index"},
            gauge={
                "axis": {"range": [0, 150]},
                "bar": {"color": "red"},
                "steps": [
                    {"range": [0, 80], "color": "#1f2937"},
                    {"range": [80, 100], "color": "#78350f"},
                    {"range": [100, 150], "color": "#991b1b"}
                ]
            }
        ))
        fig.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)
        st.warning(f"**Pressure:** {readings['pressure']} PSI (Critical > 140)")

# =========================================================
# NO-CODE BUILDER
# =========================================================

elif view == "No-Code Builder":

    st.title("🧩 No-Code HMI Builder")
    st.caption("Select widgets to build your custom dashboard — no coding required")

    selected_widgets = st.multiselect(
        "Choose Widgets to Display",
        [
            "Temperature Gauge",
            "Pressure Monitor",
            "Vibration Monitor",
            "Current Monitor",
            "Alarm Feed",
            "Motor Status",
            "Power Usage",
            "Time-to-Failure",
            "Plant Health Score",
            "AI Assistant"
        ]
    )

    st.markdown("---")

    if not selected_widgets:
        st.info("Select widgets above to build your dashboard")

    if selected_widgets:
        col1, col2 = st.columns(2)
        for i, widget in enumerate(selected_widgets):
            target = col1 if i % 2 == 0 else col2
            with target:
                if widget == "Temperature Gauge":
                    val = readings['temperature']
                    status = "🔴 CRITICAL" if val >= 100 else "🟡 WARNING" if val >= 80 else "🟢 NORMAL"
                    st.metric("🌡️ Temperature", f"{val} °C", status)

                elif widget == "Pressure Monitor":
                    val = readings['pressure']
                    status = "🔴 CRITICAL" if val >= 140 else "🟡 WARNING" if val >= 120 else "🟢 NORMAL"
                    st.metric("💨 Pressure", f"{val} PSI", status)

                elif widget == "Vibration Monitor":
                    val = readings['vibration']
                    status = "🔴 CRITICAL" if val >= 0.8 else "🟡 WARNING" if val >= 0.5 else "🟢 NORMAL"
                    st.metric("📳 Vibration", f"{val} mm/s", status)

                elif widget == "Current Monitor":
                    val = readings['current']
                    status = "🔴 CRITICAL" if val >= 8 else "🟡 WARNING" if val >= 6 else "🟢 NORMAL"
                    st.metric("⚡ Current", f"{val} A", status)

                elif widget == "Alarm Feed":
                    if root:
                        st.error(f"🚨 {root['root_cause']}")
                        st.warning(root["recommendation"])
                    else:
                        st.success("✅ No active alarms")

                elif widget == "Motor Status":
                    if root:
                        st.error("❌ Motor — FAULT DETECTED")
                    else:
                        st.success("✅ Motor — Running Normally")

                elif widget == "Power Usage":
                    st.metric("⚡ Power", f"{round(readings['current']*20,1)} kW")

                elif widget == "Time-to-Failure":
                    shown = False
                    for sensor in readings:
                        ttf = time_to_failure(sensor)
                        if ttf is not None and ttf < 120:
                            st.warning(f"⏱️ {sensor}: {ttf}s")
                            shown = True
                    if not shown:
                        st.success("No imminent failures")

                elif widget == "Plant Health Score":
                    health = 62 if root else 100
                    st.metric("🏭 Plant Health", f"{health}%")

                elif widget == "AI Assistant":
                    if st.session_state.groq_ready:
                        st.info("🤖 AURA Groq AI Online — Go to AI Chat tab")
                    else:
                        st.warning("🤖 AI Offline — Add Groq key in AI Chat")

# =========================================================
# AI CHAT — POWERED BY GROQ (FREE)
# =========================================================

elif view == "AI Chat":

    st.title("🤖 AURA AI Operations Assistant")
    st.caption("Powered by Groq AI — Free, Fast, No Credit Card")

    # Groq API Key Setup
    if not st.session_state.groq_ready:

        st.info("Connect Groq AI for full natural language support — completely free, no credit card needed.")

        with st.expander("🔑 Connect Groq AI (Free)", expanded=True):
            st.markdown("""
            **Get your FREE Groq API key in 2 minutes:**
            1. Go to [console.groq.com](https://console.groq.com)
            2. Sign up — **no credit card required**
            3. Click **API Keys** → **Create API Key**
            4. Copy and paste below

            > ✅ **14,400 free requests/day** — plenty for 24/7 plant monitoring
            """)

            api_key = st.text_input(
                "Groq API Key",
                type="password",
                placeholder="gsk_..."
            )

            if st.button("🔌 Connect Groq AI"):
                if api_key and api_key.startswith("gsk_"):
                    with st.spinner("Connecting to Groq..."):
                        if test_groq_connection(api_key):
                            st.session_state.groq_api_key = api_key
                            st.session_state.groq_ready = True
                            add_log("Groq AI connected successfully")
                            st.success("✅ Groq AI connected! Ask anything about the plant.")
                            st.rerun()
                        else:
                            st.error("Connection failed. Please check your API key and try again.")
                elif api_key and not api_key.startswith("gsk_"):
                    st.error("Invalid key format. Groq API keys start with 'gsk_'")
                else:
                    st.warning("Please enter your Groq API key")

        st.markdown("---")
        st.caption("Running in keyword mode until Groq is connected")

    else:
        col_status, col_btn = st.columns([3, 1])
        with col_status:
            st.success("✅ Groq AI Connected — Ask anything about the plant")
        with col_btn:
            if st.button("Disconnect"):
                st.session_state.groq_ready = False
                st.session_state.groq_api_key = ""
                st.rerun()

    # Current Status Summary
    with st.expander("📊 Current Plant Status", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Temperature", f"{readings['temperature']}°C")
        col2.metric("Vibration", f"{readings['vibration']}")
        col3.metric("Current", f"{readings['current']}A")
        col4.metric("Pressure", f"{readings['pressure']} PSI")
        if root:
            st.error(f"Active Issue: {root['root_cause']} — {root['recommendation']}")

    st.markdown("---")

    # Chat Interface
    st.subheader("Ask AURA Anything")

    st.caption("Quick questions:")
    qcols = st.columns(4)
    quick_questions = [
        "What is wrong with the system?",
        "Should I shut down now?",
        "How long until failure?",
        "Which zone needs attention?"
    ]

    for i, qq in enumerate(quick_questions):
        if qcols[i].button(qq, key=f"qq_{i}"):
            with st.spinner("AURA is thinking..."):
                response = chatbot(qq, readings, root)
            st.session_state.chat_history.insert(0, (qq, response))
            add_log(f"Chat: {qq[:40]}...")

    st.markdown("---")

    user_input = st.text_input(
        "Your question",
        placeholder="e.g. Why is Zone D red? Should I reduce load? What caused the pressure spike?",
        key="chat_input"
    )

    if st.button("Ask AURA 🤖", type="primary"):
        if user_input.strip():
            with st.spinner("AURA is thinking..."):
                response = chatbot(user_input, readings, root)
            st.session_state.chat_history.insert(0, (user_input, response))
            add_log(f"Chat: {user_input[:40]}...")

    # Chat History
    for q, a in st.session_state.chat_history[:8]:
        with st.container():
            st.markdown(f"**👨 Operator:** {q}")
            st.info(f"🤖 **AURA:** {a}")
            st.divider()

# =========================================================
# AUTO REFRESH
# =========================================================

time.sleep(2)
st.rerun()