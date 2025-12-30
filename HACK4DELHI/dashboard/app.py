import streamlit as st

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Smart Parking Dashboard",
    layout="wide"
)

MAX_CAPACITY = 5   # must match main.py

# ---------------- UI ----------------
st.title("🚗 Smart Parking Capacity Enforcement")
st.subheader("Municipal Corporation Live Dashboard")

st.markdown(
    """
    This dashboard shows the real-time parking status detected by the
    Smart Parking AI System installed at the parking entry/exit gate.
    """
)

st.markdown("---")

# ---------------- DEMO CONTROL ----------------
st.markdown("### 🔧 Demo Control (for Presentation)")
current_count = st.slider(
    "Simulated Live Vehicle Count",
    min_value=0,
    max_value=MAX_CAPACITY + 5,
    value=0
)

st.markdown("---")

# ---------------- STATUS DISPLAY ----------------
col1, col2, col3 = st.columns(3)

col1.metric(
    label="🚘 Vehicles Parked",
    value=current_count
)

col2.metric(
    label="🅿️ Maximum Capacity",
    value=MAX_CAPACITY
)

if current_count >= MAX_CAPACITY:
    col3.metric(
        label="🚨 Status",
        value="OVER CAPACITY"
    )
    st.error("⚠️ Parking capacity exceeded. Alert sent to MCD.")
else:
    col3.metric(
        label="✅ Status",
        value="NORMAL"
    )
    st.success("Parking is operating within allowed capacity.")

st.markdown("---")

# ---------------- FOOTER ----------------
st.markdown(
    """
    System Features
    - AI-based vehicle detection & tracking  
    - Accurate entry/exit counting  
    - Automatic capacity enforcement  
    - Email alerts to Municipal Authorities  

    _Smart Parking System – Hack4Delhi_
    """
)