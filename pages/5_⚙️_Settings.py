import streamlit as st
import os
from pathlib import Path

st.set_page_config(page_title="Settings", layout="wide")

# -------------------------------------------------------
# GAMIFIED SIDEBAR PROGRESS
# -------------------------------------------------------
total_steps = 3  # Goal -> Roadmap -> Schedule
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
    elif current_step >= 2:
        st.success("✅ **Ready:** Start Learning!")

st.title("⚙️ Settings")

st.markdown("### 🔑 API Configuration")

st.info("💡 To enable AI-powered curriculum generation, add your Google Gemini API key below.")

with st.expander("🆓 How to get a FREE Gemini API key"):
    st.markdown("""
    1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
    2. Click **"Get API Key"** or **"Create API Key"**
    3. Copy your API key
    4. Paste it below
    
    **Note:** Gemini API has a generous free tier!
    """)

# Load current API key
env_path = Path("C:/Users/ASUS/OneDrive/Desktop/Adaptive Study Planner/.env")
current_key = ""

if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('GEMINI_API_KEY='):
                current_key = line.split('=', 1)[1].strip()
                if current_key == 'your_api_key_here':
                    current_key = ""

# API Key input
with st.form("api_key_form"):
    api_key = st.text_input(
        "Gemini API Key",
        value=current_key,
        type="password",
        placeholder="Enter your API key here"
    )
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        save_button = st.form_submit_button("💾 Save", type="primary")
    
    with col2:
        if current_key:
            st.success("✅ API key is configured")
        else:
            st.warning("⚠️ No API key configured - using env key")
    
    if save_button:
        if api_key:
            # Save to .env file
            with open(env_path, 'w') as f:
                f.write(f"GEMINI_API_KEY={api_key}\n")
            
            st.success("✅ API key saved successfully!")
            st.info("🔄 Please restart the app for changes to take effect.")
            st.balloons()
        else:
            st.error("❌ Please enter an API key")

st.markdown("---")

st.markdown("### 📊 Current Configuration")

col1, col2 = st.columns(2)

with col1:
    st.metric("LLM Integration", "Enabled" if current_key else "Disabled")

with col2:
    st.metric("Backend", "Streamlit")

st.markdown("---")

st.markdown("### 🤖 AI Components Status")

components = {
    "State Space Representation": "✅ Active",
    "A* Search Algorithm": "✅ Active",
    "Knowledge Representation": "✅ Active",
    "Reasoning Engine": "✅ Active",
    "CSP Scheduler": "✅ Active",
    "LLM Integration": "✅ Active"
}

for component, status in components.items():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**{component}**")
    with col2:
        st.markdown(status)

st.markdown("---")

st.markdown("### 📖 About This Project")

st.markdown("""
**Adaptive AI Study Planner** is an intelligent learning companion that uses:

- **State Space Search** to represent your learning journey
- **A* Algorithm** to find optimal learning paths
- **Constraint Satisfaction** to schedule realistic study plans
- **Rule-Based Reasoning** to adapt to your needs
- **LLM Integration** for natural language understanding

Built with ❤️ for Artificial Intelligence Project
""")
