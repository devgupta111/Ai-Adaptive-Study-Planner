# ---------------------- 1_🎯_Set_Goal.py ----------------------
import streamlit as st
from datetime import date, timedelta
import sys, os

# allow backend imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(page_title="Set Goal", layout="wide")

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

st.title("🎯 Set Your Learning Goal")

# -------------------------------------------------------
# SESSION DEFAULTS
# -------------------------------------------------------
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "graph" not in st.session_state:
    st.session_state.graph = None
if "learning_path" not in st.session_state:
    st.session_state.learning_path = []
if "roadmap_generated" not in st.session_state:
    st.session_state.roadmap_generated = False
if "schedule_generated" not in st.session_state:
    st.session_state.schedule_generated = False

ud = st.session_state.user_data

previous_subjects = ud.get("subjects", [])
prev_unavailable_slots = ud.get("unavailable_slots", {})

# -------------------------------------------------------
# CONSTANTS
# -------------------------------------------------------
TIME_SLOTS = ["6-9 AM", "9-12 PM", "12-3 PM", "3-6 PM", "6-9 PM", "9-12 AM"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

SUBJECT_TEMPLATES = [
    "DSA", "Python", "Web Development", "Operating Systems", "Computer Networks",
    "System Design", "Machine Learning", "Databases", "AI", "Maths"
]

# -------------------------------------------------------
# SUBJECT SELECTION
# -------------------------------------------------------
st.header("📚 Subjects (Select Multiple)")
with st.expander("Choose from templates or add custom subjects", expanded=True):

    # template defaults
    template_defaults = [s for s in previous_subjects if s in SUBJECT_TEMPLATES]

    selected = st.multiselect(
        "Choose subjects",
        SUBJECT_TEMPLATES,
        default=template_defaults
    )

    prev_custom_subjects = [s for s in previous_subjects if s not in SUBJECT_TEMPLATES]
    custom_text = st.text_input(
        "Add custom subjects (comma separated)",
        value=", ".join(prev_custom_subjects)
    )

    custom_subjects = [s.strip() for s in custom_text.split(",") if s.strip()]

    subjects = list(dict.fromkeys(selected + custom_subjects))
    st.write("### Selected:", subjects if subjects else "— None —")

# -------------------------------------------------------
# TIMELINE
# -------------------------------------------------------
st.markdown("---")
st.header("📅 Timeline")

col1, col2 = st.columns(2)
with col1:
    deadline = st.date_input(
        "Target Completion Date",
        value=ud.get("deadline", date.today() + timedelta(days=45)),
        min_value=date.today()
    )
with col2:
    study_hours_per_day = st.slider(
        "Study hours per day",
        1, 8,
        value=ud.get("study_hours_per_day", 3)
    )

# -------------------------------------------------------
# SESSION PREFERENCES
# -------------------------------------------------------
st.markdown("---")
st.header("⏱️ Session Preferences")

col1, col2 = st.columns(2)
with col1:
    session_options = {"25 min (Pomodoro)": 25, "45 min": 45, "60 min": 60, "90 min": 90}
    default_session = ud.get("session_length", 45)
    try:
        idx = list(session_options.values()).index(default_session)
    except ValueError:
        idx = 1
    session_label = st.selectbox("Session length", list(session_options.keys()), index=idx)
    session_length = session_options[session_label]

with col2:
    break_map = {"5 min": 5, "10 min": 10, "15 min": 15, "20 min": 20}
    default_break = ud.get("break_length", 10)
    try:
        idx_break = list(break_map.values()).index(default_break)
    except ValueError:
        idx_break = 1

    break_label = st.selectbox("Break duration", list(break_map.keys()), index=idx_break)
    break_length = break_map[break_label]

peak_hours = st.multiselect("Peak focus hours", TIME_SLOTS, default=ud.get("peak_hours", ["9-12 PM"]))

# -------------------------------------------------------
# AVAILABLE SLOTS (FINAL FIXED VERSION)
# -------------------------------------------------------
st.markdown("---")
st.header("🕒 Available Study Slots (per day)")
st.caption("Select the slots you CAN study. If you leave all empty, the day becomes fully unavailable.")

available_slots = {}
cols = st.columns(2)

for i, day in enumerate(WEEKDAYS):
    with cols[i % 2].expander(day):

        # Previous unavailable → derive available
        prev_unavail = set(prev_unavailable_slots.get(day, []))
        if prev_unavail:
            previous_available = [s for s in TIME_SLOTS if s not in prev_unavail]
        else:
            previous_available = []  # default: none selected

        sel = st.multiselect(
            f"{day} — available slots",
            TIME_SLOTS,
            default=previous_available,
            key=f"avail_{day}"
        )

        available_slots[day] = sel

# Convert available → unavailable
unavailable_slots = {}
unavailable_days = []

for day in WEEKDAYS:
    sel = set(available_slots[day])

    if len(sel) == 0:
        # fully unavailable day
        unavailable_slots[day] = list(TIME_SLOTS)
        unavailable_days.append(day)
    else:
        unavailable_slots[day] = [s for s in TIME_SLOTS if s not in sel]

# -------------------------------------------------------
# OTHER PREFS
# -------------------------------------------------------
st.markdown("---")
learning_style = st.selectbox(
    "Learning Style",
    ["Mixed", "Visual", "Hands-on", "Reading"],
    index=["Mixed", "Visual", "Hands-on", "Reading"].index(
        ud.get("learning_style", "Mixed")
    )
)

difficulty_preference = st.selectbox(
    "Pace Preference",
    ["Start easy", "Balanced progression", "Jump ahead"],
    index=["Start easy", "Balanced progression", "Jump ahead"].index(
        ud.get("difficulty_preference", "Balanced progression")
    )
)

# -------------------------------------------------------
# SUBMIT BUTTON
# -------------------------------------------------------
if st.button("🚀 Generate Learning Roadmap", type="primary"):

    if not subjects:
        st.error("Please select at least one subject.")
        st.stop()
    
    # ============================================================
    # VALIDATION: Check if any study time is available
    # ============================================================
    total_available_slots = sum(len(slots) for slots in available_slots.values())
    
    if total_available_slots == 0:
        st.error("❌ No study slots available!")
        st.warning("""You haven't selected any available study slots. 
        Please go back to the 'Available Study Slots' section and select at least 
        one time slot on one day.""")
        st.stop()
    
    # Calculate total available hours
    total_hours_per_week = total_available_slots * 3  # Each slot is 3 hours
    days_until_deadline = (deadline - date.today()).days
    weeks_available = max(1, days_until_deadline / 7)
    estimated_total_hours = total_hours_per_week * weeks_available * (study_hours_per_day / len(TIME_SLOTS))
    
    if estimated_total_hours < 10:
        st.warning(f"""⚠️ **Very Limited Study Time Detected**
        
        Based on your settings:
        - Available slots per week: {total_available_slots}
        - Estimated total study hours: {estimated_total_hours:.1f}h
        - This may not be enough to cover all topics!
        
        **Recommendation:** Extend deadline or add more study slots.
        """)
    
    # ============================================================
    # VALIDATION: Check if any study time is available
    # ============================================================
    total_available_slots = sum(len(slots) for slots in available_slots.values())
    
    if total_available_slots == 0:
        st.error("❌ No study slots available!")
        st.warning("""You haven't selected any available study slots. 
        Please go back to the 'Available Study Slots' section and select at least 
        one time slot on one day.""")
        st.stop()
    
    # Calculate total available hours per week
    total_hours_per_week = total_available_slots * 3 * study_hours_per_day / len(TIME_SLOTS)
    days_until_deadline = (deadline - date.today()).days
    weeks_available = max(1, days_until_deadline / 7)
    estimated_total_hours = total_hours_per_week * weeks_available
    
    if estimated_total_hours < 10:
        st.warning(f"""⚠️ **Very Limited Study Time Detected**
        
        Based on your settings:
        - Available slots per week: {total_available_slots}
        - Estimated total study hours: {estimated_total_hours:.1f}h
        - This may not be enough to cover all topics!
        
        Consider:
        - Extending your deadline
        - Adding more study slots
        - Increasing daily study hours
        """)
    
    # ============================================================
    # ETHICS CHECK - Validate against health constraints
    # ============================================================
    from backend.ethics import EthicsGuard
    from backend.db import PersistenceManager
    
    pm_check = PersistenceManager()
    
    # Create temp user model for ethics check
    class TempUser:
        def __init__(self, data):
            for k, v in data.items():
                setattr(self, k, v)
    
    temp_user_data = {
        "study_hours_per_day": study_hours_per_day,
        "session_length": session_length,
        "break_length": break_length,
        "peak_hours": peak_hours,
        "unavailable_days": unavailable_days,
    }
    
    guard = EthicsGuard()
    is_safe, ethical_warnings = guard.check_health_constraints(TempUser(temp_user_data))
    
    if ethical_warnings:
        st.markdown("---")
        st.markdown("### ⚖️ Ethical AI Safety Check")
        
        for warning in ethical_warnings:
            if "CRITICAL" in warning:
                st.error(warning)
            else:
                st.warning(warning)
        
        pm_check.log_event("Ethics", f"Raised {len(ethical_warnings)} health warnings", 
                          f"Safe: {is_safe}")
        
        if not is_safe:
            st.markdown("---")
            st.markdown("### 💡 Healthier Alternative")
            suggestion = guard.suggest_healthier_alternative(TempUser(temp_user_data))
            st.info(suggestion["reasoning"])
            
            st.json(suggestion)
            st.stop()  # Refuse to proceed
        else:
            st.info("⚠️ The AI will proceed, but **strongly recommends** adjusting for your well-being.")
            
            with st.expander("📚 Why These Constraints Matter"):
                st.markdown(guard.explain_ethics())
    
    # ============================================================
    st.session_state.schedule_generated = False

    st.session_state.user_data = {
        "subjects": subjects,
        "goal": ", ".join(subjects),
        "deadline": deadline,
        "study_hours_per_day": study_hours_per_day,
        "session_length": session_length,
        "break_length": break_length,
        "peak_hours": peak_hours,
        "unavailable_slots": unavailable_slots,
        "unavailable_days": unavailable_days,
        "learning_style": learning_style,
        "difficulty_preference": difficulty_preference,
        "completed_topics": [],
        "topic_weakness": ud.get("topic_weakness", {}),
        "priority_weights": {
            "prerequisites": 1.0,
            "deadline": 0.8,
            "difficulty": 0.7,
            "weakness": 0.5,
        },
    }

    # ============================================================
    # INTELLIGENT LOADING STATE - Show AI steps in real-time
    # ============================================================
    with st.status("🤖 AI Agent Working...", expanded=True) as status:
        # Backend imports
        from backend.state_graph import StudyGraph
        from backend.llm_helper import LLMHelper
        from backend.user_model import UserModel
        from backend.a_star_planner import AStarPlanner
        from backend.meta_reasoner import MetaReasoner
        
        # Step 1: LLM Curriculum Generation
        st.write("🧠 Consulting LLM for curriculum breakdown...")
        llm = LLMHelper()
        curriculum = llm.generate_curriculum(st.session_state.user_data["goal"])
        st.write(f"   ✅ Generated {len(curriculum)} topics")
        
        # Step 2: Knowledge Graph Construction
        st.write("🕸️ Constructing Knowledge Graph nodes...")
        graph = StudyGraph()
        for t in curriculum:
            graph.add_topic(
                topic_id=t.get("id", t.get("title")),
                title=t["title"],
                prerequisites=t.get("prerequisites", []),
                difficulty=t.get("difficulty", 0.5),
                category=t.get("category", "General"),
                estimated_hours=t.get("hours", 2),
                description=t.get("description", ""),
                subtopics=t.get("subtopics", [])
            )
        st.session_state.graph = graph
        st.write(f"   ✅ Built graph with {len(curriculum)} nodes")
        
        # Step 3: Priority Calculation
        st.write("📊 Calculating topic priorities using reasoning engine...")
        user_model_for_planner = UserModel(**st.session_state.user_data)
        priorities = graph.recalculate_priorities(user_model_for_planner)
        st.write(f"   ✅ Prioritized based on deadline ({user_model_for_planner.get_days_until_deadline()} days)")
        
        pm_reasoning = PersistenceManager()
        pm_reasoning.log_event("Reasoning", 
                              f"Calculated priorities for {len(priorities)} topics",
                              f"Deadline: {user_model_for_planner.get_days_until_deadline()} days")
        
        # Step 4: A* Pathfinding
        st.write("⚡ Running A* Search for optimal path...")
        planner = AStarPlanner(graph, user_model_for_planner)
        path = planner.find_optimal_path()
        
        if not path:
            status.update(label="❌ Path Generation Failed", state="error", expanded=True)
            st.error("Learning path could not be generated.")
            st.stop()
        
        st.write(f"   ✅ Found optimal path with {len(path)} topics")
        
        # Step 5: Meta-Reasoning (Fatigue Filter)
        st.write("🧠 Applying meta-reasoning to optimize cognitive load...")
        meta = MetaReasoner(graph)
        original_path = path.copy()
        path = meta.apply_fatigue_filter(path)
        
        st.session_state.original_path = original_path
        st.session_state.learning_path = path
        
        if original_path != path:
            reordered_count = len([i for i, (o, p) in enumerate(zip(original_path, path)) if o != p])
            st.write(f"   ✅ Reordered {reordered_count} topics to prevent fatigue")
            
            pm_meta = PersistenceManager()
            pm_meta.log_event("Meta", "Applied fatigue filter to learning path",
                            f"Reordered {reordered_count} topics")
        else:
            st.write("   ✅ Path already optimized")
        
        # Step 6: Persistence
        st.write("💾 Saving roadmap to database...")
        pm_save = PersistenceManager()
        pm_save.save_state('graph', graph)
        pm_save.save_state('user_data', st.session_state.user_data)
        pm_save.save_state('learning_path', st.session_state.learning_path)
        pm_save.log_event("A*", f"Generated optimal path with {len(path)} topics", 
                         f"First: {path[0] if path else 'N/A'}")
        st.write("   ✅ State persisted")
        
        # Complete!
        st.session_state.roadmap_generated = True
        status.update(label="✅ Roadmap Generated!", state="complete", expanded=False)
    
    st.success("🎉 Your personalized learning roadmap is ready! Scroll down to rate your confidence.")
    st.rerun()

# -------------------------------------------------------
# CONFIDENCE FORM + ROADMAP VIEW WITH SUBTOPICS
# -------------------------------------------------------
if st.session_state.roadmap_generated and st.session_state.graph:
    st.markdown("---")
    st.subheader("🧭 Roadmap Overview (with subtopics)")

    graph = st.session_state.graph
    learning_path = st.session_state.learning_path

    # Show roadmap with subtopics
    for idx, topic in enumerate(learning_path, start=1):
        data = graph.get_topic_data(topic)
        title = data.get("title", topic)
        subs = data.get("subtopics", [])
        st.markdown(f"**{idx}. {title}**")
        if subs:
            st.markdown("📝 Subtopics: " + ", ".join(subs[:5]))
        st.markdown("---")

    st.subheader("💯 Rate Your Confidence")

    prev_weak = st.session_state.user_data.get("topic_weakness", {})

    with st.form("conf_form"):
        weakness_map = {}
        for topic in learning_path:
            data = graph.get_topic_data(topic)
            title = data.get("title", topic)
            subs = data.get("subtopics", [])
            prev_w = prev_weak.get(topic, 0.4)
            conf_default = max(1, min(5, int(6 - prev_w * 5)))

            if subs:
                label = f"{title} — confidence (e.g. {', '.join(subs[:2])})"
            else:
                label = f"{title} — confidence"

            conf = st.slider(label, 1, 5, conf_default)
            weakness_map[topic] = (6 - conf) / 5

        save = st.form_submit_button("Save Weakness Ratings")

    if save:
        st.session_state.user_data["topic_weakness"] = weakness_map
        st.success("Weakness saved. Go to **View Schedule**.")
        st.rerun()
