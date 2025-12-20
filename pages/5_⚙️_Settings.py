import streamlit as st
import os

st.set_page_config(page_title="Settings", layout="wide")

# -------------------------------------------------------
# GAMIFIED SIDEBAR PROGRESS
# -------------------------------------------------------
total_steps = 3
current_step = 0
if st.session_state.get('roadmap_generated'):
    current_step = 1
if st.session_state.get('schedule_generated'):
    current_step = 2

progress = current_step / total_steps

with st.sidebar:
    st.markdown("### 🧬 Your Progress")
    st.progress(progress)

    if current_step == 0:
        st.info("👇 **Start:** Set your Goal")
    elif current_step == 1:
        st.warning("👉 **Next:** Generate Schedule")
    else:
        st.success("✅ **Ready:** Start Learning!")

# -------------------------------------------------------
# SETTINGS UI
# -------------------------------------------------------
st.title("⚙️ Settings")
st.markdown("### 🔑 API Configuration")

st.info("💡 Gemini API key is securely handled using environment variables on cloud.")

with st.expander("🆓 How to get a FREE Gemini API key"):
    st.markdown("""
    1. Go to https://makersuite.google.com/app/apikey
    2. Create an API key
    3. Paste it below
    """)

# Load key from env or session
env_key = os.getenv("GEMINI_API_KEY", "")
session_key = st.session_state.get("GEMINI_API_KEY", "")
current_key = session_key or env_key

# Input form
with st.form("api_key_form"):
    api_key = st.text_input(
        "Gemini API Key",
        value=current_key,
        type="password",
        placeholder="Enter your API key"
    )

    save = st.form_submit_button("💾 Save")

    if save:
        if api_key:
            st.session_state["GEMINI_API_KEY"] = api_key
            st.success("✅ API key loaded into session")
        else:
            st.error("❌ Please enter a valid API key")

# Status
st.markdown("---")
st.markdown("### 📊 Current Configuration")

col1, col2 = st.columns(2)
with col1:
    st.metric("LLM Integration", "Enabled" if current_key else "Disabled")
with col2:
    st.metric("Backend", "Streamlit Cloud")

# AI Components
st.markdown("---")
st.markdown("### 🤖 AI Components Status")

components = [
    "State Space Representation",
    "A* Search Algorithm",
    "Knowledge Representation",
    "Reasoning Engine",
    "CSP Scheduler",
    "LLM Integration"
]

for comp in components:
    col1, col2 = st.columns([3, 1])
    col1.markdown(f"**{comp}**")
    col2.markdown("✅ Active")

st.markdown("---")
st.markdown("""
### 📖 About This Project
Adaptive AI Study Planner uses classical and modern AI techniques to generate
personalized, ethical, and realistic study plans.
""")
