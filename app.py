import streamlit as st
from datetime import datetime
from backend.db import PersistenceManager

# Page config
st.set_page_config(
    page_title="Adaptive AI Study Planner",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# PERSISTENCE LAYER - Load previous state if available
# ============================================================
pm = PersistenceManager()

# Initialize session state
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
if 'roadmap_generated' not in st.session_state:
    st.session_state.roadmap_generated = False
if 'schedule_generated' not in st.session_state:
    st.session_state.schedule_generated = False
if 'graph' not in st.session_state:
    st.session_state.graph = None
if 'learning_path' not in st.session_state:
    st.session_state.learning_path = []
if 'schedule' not in st.session_state:
    st.session_state.schedule = None

# ✅ PERSISTENCE: Attempt to restore previous session
if st.session_state.graph is None:
    loaded_graph = pm.load_state('graph')
    if loaded_graph:
        st.session_state.graph = loaded_graph
        st.session_state.roadmap_generated = True
        pm.log_event("System", "Restored graph from previous session", f"{len(loaded_graph.graph.nodes)} topics")

if not st.session_state.user_data:
    loaded_user = pm.load_state('user_data')
    if loaded_user:
        st.session_state.user_data = loaded_user
        pm.log_event("System", "Restored user data from previous session", f"Goal: {loaded_user.get('goal', 'N/A')}")

if not st.session_state.learning_path:
    loaded_path = pm.load_state('learning_path')
    if loaded_path:
        st.session_state.learning_path = loaded_path

# Main page
st.title("📚 Adaptive AI Study Planner")
st.markdown("### Your Personal AI-Powered Learning Companion")

# Sidebar
with st.sidebar:
    st.header("🎯 Quick Navigation")
    st.markdown("---")
    
    if st.session_state.roadmap_generated:
        st.success("✅ Roadmap Generated")
        # --- RESET BUTTON ---
        st.markdown("---")
        if st.button("🔄 Reset All Data", help="Clear all progress, goals, and settings for a fresh start."):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            # Clear persistent state from database
            pm.clear_state('graph')
            pm.clear_state('user_data')
            pm.clear_state('learning_path')
            pm.log_event("System", "User triggered full reset", "All user/session data cleared")
            st.success("✅ All data reset! Please refresh the page to start over.")
            st.stop()
    else:
        st.warning("⏳ No roadmap yet")
    
    if st.session_state.schedule_generated:
        st.success("✅ Schedule Created")
    else:
        st.warning("⏳ No schedule yet")
    
    st.markdown("---")
    st.info("""
    **How it works:**
    1. Set your learning goal
    2. Configure preferences
    3. AI generates roadmap
    4. Get personalized schedule
    5. Track progress
    """)
    
    # ============================================================
    # TRANSPARENCY LAYER - Show AI Thinking
    # ============================================================
    st.markdown("---")
    st.header("🧠 Agent Thoughts")
    st.caption("Real-time log of AI decisions")
    
    recent_logs = pm.get_recent_logs(5)
    if recent_logs:
        for module, msg, timestamp in recent_logs:
            # Format timestamp cleanly
            try:
                t_str = timestamp.strftime("%H:%M:%S")
            except:
                t_str = str(timestamp)[:8]
            
            # Icon mapping
            icon_map = {
                "Reasoning": "🔄",
                "CSP": "📅",
                "A*": "🎯",
                "Meta": "🧠",
                "Ethics": "⚖️",
                "Persistence": "💾",
                "System": "⚙️",
                "Explainability": "💬"
            }
            icon = icon_map.get(module, "🤖")
            
            st.sidebar.markdown(f"**{t_str} {icon} [{module}]**")
            st.sidebar.caption(msg)
            st.sidebar.markdown("---")
    else:
        st.sidebar.caption("No recent activity")

# Main content
col1, col2, col3 = st.columns(3)

with col1:
    completed = len(st.session_state.user_data.get('completed_topics', [])) if st.session_state.user_data else 0
    total = len(st.session_state.learning_path) if st.session_state.learning_path else 0
    st.metric("Topics Completed", f"{completed}/{total}")

with col2:
    st.metric("Study Streak", "0 days")

with col3:
    st.metric("Total Hours", "0h")

st.markdown("---")

# Welcome section
if not st.session_state.roadmap_generated:
    st.info("👋 Welcome! Start by setting your learning goal using the **Set Goal** page in the sidebar.")
    
    with st.expander("🤖 What makes this AI-powered?"):
        st.markdown("""
        This planner uses advanced AI techniques:
        - **State Space Representation**: Your learning path as an intelligent graph
        - **A* Search Algorithm**: Finds optimal topic order
        - **Constraint Satisfaction**: Creates realistic schedules
        - **Rule-Based Reasoning**: Adapts to deadlines and habits
        - **Spaced Repetition**: Optimizes long-term retention
        - **LLM Integration**: Natural language understanding
        """)
        
    with st.expander("📋 AI Components"):
        st.markdown("""
        **✅ State Space Search:**
        - Graph representation of topics
        - A* algorithm for optimal path finding
        
        **✅ Knowledge Representation:**
        - User model with preferences and constraints
        - Rule-based knowledge base
        
        **✅ Reasoning Engine:**
        - Priority calculation based on deadlines
        - Difficulty adjustment rules
        - Spaced repetition logic
        
        **✅ Constraint Satisfaction (CSP):**
        - Schedule generation with constraints
        - Time slot allocation
        - Conflict resolution
        
        **✅ Learning & Adaptation:**
        - User feedback integration
        - Dynamic plan adjustment
        """)

else:
    st.success("🎉 Your personalized learning plan is ready!")
    st.markdown("Navigate using the sidebar to view your roadmap and schedule.")
    
    if st.session_state.learning_path:
        st.subheader("📊 Your Learning Path Overview")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("**Next Topics to Study:**")
            completed_topics = st.session_state.user_data.get('completed_topics', [])
            next_topics = [t for t in st.session_state.learning_path if t not in completed_topics][:5]
            
            for i, topic in enumerate(next_topics, 1):
                st.markdown(f"{i}. `{topic}`")
        
        with col2:
            total_topics = len(st.session_state.learning_path)
            completed = len(completed_topics)
            progress = (completed / total_topics * 100) if total_topics > 0 else 0
            
            st.metric("Progress", f"{progress:.1f}%")
            st.progress(progress / 100)

# Footer
st.markdown("---")
st.caption("Powered by AI • Built with Streamlit")
