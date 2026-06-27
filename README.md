# AURA HMI v3.0 – AI-Powered Industrial HMI 🏭

A next-generation industrial Human-Machine Interface built with Streamlit and Groq AI.  
Monitors 4 live sensors, prioritises alarms using a scoring algorithm, predicts time-to-failure,  
performs root cause analysis, and supports natural-language plant diagnostics via LLM chatbot.

---

## What it does

- Simulates real-time sensor data (temperature, vibration, current, pressure) with a  
  progressive failure ramp starting at cycle 20
- **3-state system:** NORMAL → WARNING (0–2 sec debounce) → FAULT with auto-escalation
- **AI alarm prioritisation:** scores each sensor by severity + frequency + criticality weighting
- **Root cause engine:** maps multi-sensor critical combinations to fault diagnoses
- **Predictive failure:** linear trend extrapolation over last 10 readings → estimated seconds to threshold
- **Groq LLM chatbot:** sends full plant context (readings, state, logs, TTF) to `llama-3.3-70b-versatile`
- **Keyword fallback chatbot:** works offline when Groq is not connected
- **Role-based views:** Operator / Engineer / Manager each see different dashboard tabs
- **No-Code Builder:** drag-select widgets to build a custom dashboard without writing code

---

## Dashboard views

| View | Role | What it shows |
|---|---|---|
| Plant Overview | All | Zone map, plant health %, AI insights, TTF alerts |
| AI Alarm Center | Operator, Engineer | Priority-scored alarm cards with acknowledge/snooze/escalate |
| Maintenance | Engineer | Sensor trends (Plotly), TTF predictions, priority scores |
| Emergency | Operator, Engineer | Shutdown button, fire suppression, gauge, maintenance alert |
| No-Code Builder | Engineer | Widget selector — build custom HMI without code |
| AI Chat | All | Groq LLM or keyword chatbot with quick-question buttons |

---

## Alarm priority scoring

```python
score = (severity × 0.5) + (frequency × 0.3) + (criticality × 0.2)
```

| Factor | How it's calculated |
|---|---|
| Severity | 1 = normal, 2 = warning, 3 = critical |
| Frequency | fraction of last 100 readings above warning threshold |
| Criticality | temperature 1.0, vibration 0.9, current 0.8, pressure 0.7 |

---

## Root cause logic

| Sensors in critical | Diagnosis |
|---|---|
| Temperature + Vibration | Motor Bearing Failure |
| Temperature + Current | Electrical Overload |
| Pressure alone | Pressure System Anomaly |

---

## Sensor thresholds

| Sensor | Warning | Critical |
|---|---|---|
| Temperature | 80 °C | 100 °C |
| Vibration | 0.5 mm/s | 0.8 mm/s |
| Current | 6 A | 8 A |
| Pressure | 120 PSI | 140 PSI |

---

## Groq AI setup (free)

1. Go to [console.groq.com](https://console.groq.com) — no credit card required
2. Create an API key (`gsk_...`)
3. Paste it in the **AI Chat** tab → Connect
4. 14,400 free requests/day — sufficient for continuous plant monitoring

Model used: `llama-3.3-70b-versatile` at temperature 0.3  
Falls back to keyword chatbot automatically if Groq is offline.

---

## Installation

```bash
pip install streamlit pandas numpy plotly requests
streamlit run aura_hmi.py
```

---

## What I'd improve next

- Replace simulated sensor data with real MQTT/OPC-UA input
- Persist alarm history and chat logs to SQLite or CSV
- Add user authentication for role-based access control
- Deploy on Streamlit Cloud for remote plant monitoring
- Add SMS/email alerts when critical thresholds are breached
