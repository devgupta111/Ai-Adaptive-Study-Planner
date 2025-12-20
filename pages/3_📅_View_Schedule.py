# ---------------------- 3_📅_View_Schedule.py ----------------------
import streamlit as st
import pandas as pd
from datetime import datetime, time

st.set_page_config(page_title="View Schedule", layout="wide")
st.title("📅 Weekly Study Schedule")

# ------------------------------------------------------
# Guard
# ------------------------------------------------------
if not st.session_state.get("roadmap_generated", False):
    st.warning("⚠️ Roadmap not generated. Go to **Set Goal**.")
    st.stop()

user_data = st.session_state.user_data
graph = st.session_state.graph
learning_path = st.session_state.learning_path
completed_topics = user_data.get("completed_topics", [])

st.success("🎯 Your Weekly AI Schedule")

# ------------------------------------------------------
# Generate schedule button
# ------------------------------------------------------
if not st.session_state.get("schedule_generated", False):
    if st.button("🚀 Generate Weekly Schedule", type="primary"):
        st.session_state.schedule_generated = True
        st.rerun()

if not st.session_state.get("schedule_generated", False):
    st.info("Click **Generate Weekly Schedule**.")
    st.stop()

# ------------------------------------------------------
# Build UserModel for CSP
# ------------------------------------------------------
from backend.user_model import UserModel
from backend.scheduler import SchedulerCSP

deadline_date = user_data.get("deadline")

if isinstance(deadline_date, datetime):
    deadline_dt = deadline_date
else:
    try:
        deadline_dt = datetime.combine(deadline_date, time.min)
    except Exception:
        deadline_dt = datetime.now()

try:
    user_model = UserModel(
        goal=user_data["goal"],
        deadline=deadline_dt,
        study_hours_per_day=user_data["study_hours_per_day"],
        session_length=user_data["session_length"],
        break_length=user_data["break_length"],
        peak_hours=user_data["peak_hours"],
        unavailable_days=user_data["unavailable_days"],
        unavailable_slots=user_data["unavailable_slots"],
        learning_style=user_data["learning_style"],
        difficulty_preference=user_data["difficulty_preference"],
        completed_topics=completed_topics,
        topic_weakness=user_data.get("topic_weakness", {}),
        priority_weights=user_data.get("priority_weights", {}),
    )
except Exception:
    class SimpleUser:
        pass
    user_model = SimpleUser()
    for k, v in user_data.items():
        setattr(user_model, k, v)

# ------------------------------------------------------
# Run CSP
# ------------------------------------------------------
from backend.db import PersistenceManager
pm_csp = PersistenceManager()

scheduler = SchedulerCSP(graph, user_model, learning_path)
weekly_schedule = scheduler.generate_schedule()

pm_csp.log_event("CSP", 
                f"Generated schedule: {sum(1 for d in weekly_schedule.values() if isinstance(d, list))} days planned",
                f"Sessions created across week")

# ✅ CRITICAL: Check for dropped topics and warn user
dropped_topics = weekly_schedule.get("_dropped_topics", [])
dropped_parts = weekly_schedule.get("_dropped_parts", [])

if dropped_topics:
    # Check if ALL topics were dropped (critical failure)
    total_topics_attempted = len(learning_path)
    
    if len(dropped_topics) == total_topics_attempted:
        st.error(f"🚨 **CRITICAL: ALL {len(dropped_topics)} topics could not fit in your schedule!**")
        
        st.markdown("---")
        st.markdown("### 🔍 Root Cause Analysis")
        
        # Calculate metrics
        from datetime import date, timedelta
        from math import ceil
        
        days_until_deadline = (user_data['deadline'] - date.today()).days
        study_hours_per_day = user_data.get('study_hours_per_day', 3)
        total_hours_needed = sum(graph.get_topic_data(t)['estimated_hours'] for t in learning_path)
        max_possible = days_until_deadline * study_hours_per_day
        
        # Calculate actual available slots
        all_slots = ['6-9 AM', '9-12 PM', '12-3 PM', '3-6 PM', '6-9 PM', '9-12 AM']
        weekdays_list = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        unavail_slots = user_data.get('unavailable_slots', {})
        total_available_slots = sum(
            len([s for s in all_slots if s not in unavail_slots.get(day, [])])
            for day in weekdays_list
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Hours Needed", f"{total_hours_needed:.0f}h")
            st.metric("Max Possible", f"{max_possible:.0f}h")
        with col2:
            st.metric("Available Slots/Week", total_available_slots)
            st.metric("Study Hours/Day", f"{study_hours_per_day}h")
        with col3:
            st.metric("Days to Deadline", f"{days_until_deadline}")
            weeks = days_until_deadline / 7
            st.metric("Weeks Available", f"{weeks:.1f}")
        
        st.markdown("---")
        
        # Diagnose the specific problem
        if max_possible < total_hours_needed:
            deficit = total_hours_needed - max_possible
            st.error(f"**⏰ Time Deficit: {deficit:.0f}h SHORT** - Your deadline is mathematically impossible!")
            
            st.markdown("### 💡 Solution: Pick ONE of these options")
            
            tab1, tab2 = st.tabs(["📅 Extend Deadline", "⏰ Increase Daily Hours"])
            
            with tab1:
                min_days_needed = ceil(total_hours_needed / study_hours_per_day)
                new_deadline = date.today() + timedelta(days=min_days_needed)
                st.success(f"**Extend deadline to {min_days_needed} days from now**")
                st.info(f"New date: {new_deadline.strftime('%B %d, %Y')}")
            
            with tab2:
                min_hours_needed = ceil(total_hours_needed / days_until_deadline)
                st.success(f"**Increase to {min_hours_needed} hours per day**")
                st.info(f"Currently: {study_hours_per_day}h/day")
        
        elif total_available_slots < 6:
            st.error(f"**🕒 Too Few Time Slots: Only {total_available_slots} slots/week available**")
            st.warning("""
            You have enough total hours, but too few time slots to spread the work across!
            
            **Solution:** Enable more time slots per day in the "Available Study Slots" section.
            
            Example: If you only selected "6-9 PM" each day, add "3-6 PM" as well.
            """)
        
        else:
            st.warning("The scheduler couldn't fit topics despite having enough total time.")
            st.info("""
            Possible causes:
            - Session length too short to fit topics efficiently
            - Break times consuming too much capacity
            - Slots are too spread out across days
            """)
        
        st.markdown("---")
        if st.button("← Back to Set Goal", type="primary"):
            st.switch_page("pages/1_🎯_Set_Goal.py")
        
        st.stop()  # Don't show empty schedule
    
    # Partial failure (some topics fit)
    st.error(f"⚠️ **Constraint Violation Detected**: {len(dropped_topics)} topic(s) could not fit in your schedule!")
    
    with st.expander("🔍 View Scheduling Conflicts", expanded=True):
        st.markdown("**The following topics need more time slots:**")
        
        for dt in dropped_topics:
            st.markdown(f"- **{dt['title']}** ({dt['hours']}h)")
            st.caption(f"   Reason: {dt['reason']}")
        
        st.markdown("---")
        st.markdown("**💡 Recommended Actions:**")
        st.markdown("1. ⏰ **Extend Deadline** - Give yourself more time")
        st.markdown("2. 📅 **Add More Study Hours** - Increase daily availability")
        st.markdown("3. 🎯 **Remove Some Topics** - Focus on essentials first")
        st.markdown("4. ⏱️ **Increase Session Length** - Study in longer blocks")
        
        if st.button("🔄 Go Back to Settings"):
            st.session_state.schedule_generated = False
            st.switch_page("pages/1_🎯_Set_Goal.py")

weekly_schedule.pop("_future_reviews", None)
weekly_schedule.pop("_dropped_topics", None)
weekly_schedule.pop("_dropped_parts", None)
weeks_available = weekly_schedule.pop("_weeks_available", 1)
current_week_schedule = weekly_schedule.pop("_current_week_schedule", {})

TIME_SLOTS = ["6-9 AM", "9-12 PM", "12-3 PM", "3-6 PM", "6-9 PM", "9-12 AM"]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# ------------------------------------------------------
# Multi-Week Schedule Display
# ------------------------------------------------------
st.markdown(f"### 📅 Study Schedule ({weeks_available} Week{'s' if weeks_available > 1 else ''})")

# Create tabs for each week
week_tabs = st.tabs([f"Week {i}" for i in range(1, weeks_available + 1)])

for week_num, tab in enumerate(week_tabs, 1):
    with tab:
        st.markdown(f"#### Week {week_num} Schedule")
        
        # Build display for this week
        for day in WEEKDAYS:
            week_day_key = f"Week {week_num} - {day}"
            sessions = weekly_schedule.get(week_day_key, [])
            
            # Unavailable day
            if day in user_data.get("unavailable_days", []):
                st.markdown(f"**{day}**: ❌ Unavailable")
                continue

            if not isinstance(sessions, list) or len(sessions) == 0:
                st.markdown(f"**{day}**: — No sessions —")
                continue

            # Group by time slot
            grouped = {slot: [] for slot in TIME_SLOTS}
            for s in sessions:
                grouped[s["time"]].append(s)

            # Display sessions for this day
            with st.expander(f"📅 {day} ({len(sessions)} sessions)", expanded=(week_num == 1)):
                for slot in TIME_SLOTS:
                    slot_sessions = grouped.get(slot, [])
                    if not slot_sessions:
                        continue

                    st.markdown(f"### ⏰ {slot}")

                    for s in slot_sessions:
                        emoji = "⭐" if s.get("is_peak") else "📘"
                        base_title = s.get("title", "")
                        duration = s.get("duration", user_data.get("session_length", 45))
                        brk = s.get("break_after", user_data.get("break_length", 10))
                        tid = s.get("topic_id", "")
                        
                        # Get subtopic for this specific part
                        subtopic_text = s.get("subtopic")
                        if not subtopic_text:
                            # Fallback: get all subtopics from graph
                            data = graph.get_topic_data(tid)
                            all_subs = data.get("subtopics", [])
                            if all_subs:
                                subtopic_text = ", ".join(all_subs[:3])  # Show first 3
                        
                        # Extract base topic name without part number
                        # e.g., "Data Storage (Part 3/16)" -> "Data Storage"
                        topic_name = base_title.split(" (Part ")[0] if " (Part " in base_title else base_title
                        
                        # Build display title with subtopic instead of part number
                        if subtopic_text:
                            display_title = f"{topic_name}: {subtopic_text}"
                        else:
                            display_title = base_title  # Fallback to original with part number

                        st.markdown(f"- {emoji} **{display_title}**")
                        st.caption(f"  ⏱ {duration} min + {brk} min break")
                        st.caption(f"  🔖 Topic: `{tid}`")
                        st.markdown("")

st.markdown("---")

# ------------------------------------------------------
# Legacy Table View (Week 1 only for backwards compatibility)
# ------------------------------------------------------
st.markdown("#### 📋 Week 1 Table View")

table_rows = []

for day in WEEKDAYS:

    # Unavailable day
    if day in user_data.get("unavailable_days", []):
        table_rows.append({"Day": f"❌ {day}", "Sessions": "Unavailable"})
        continue

    week_day_key = f"Week 1 - {day}"
    sessions = weekly_schedule.get(week_day_key, [])

    if not isinstance(sessions, list) or len(sessions) == 0:
        table_rows.append({"Day": day, "Sessions": "— No sessions —"})
        continue

    # --- GROUP BY SLOT ---
    grouped = {slot: [] for slot in TIME_SLOTS}
    for s in sessions:
        grouped[s["time"]].append(s)

    # Format output with subtopics
    block = ""
    for slot in TIME_SLOTS:
        slot_sessions = grouped.get(slot, [])
        if not slot_sessions:
            continue

        # Slot heading
        block += f"### ⏰ {slot}\n"

        for s in slot_sessions:
            emoji = "⭐" if s.get("is_peak") else "📘"
            base_title = s.get("title", "")
            duration = s.get("duration", user_data.get("session_length", 45))
            brk = s.get("break_after", user_data.get("break_length", 10))
            tid = s.get("topic_id", "")

            # Get subtopic for this specific part
            subtopic_text = s.get("subtopic")
            if not subtopic_text and tid:
                # Fallback: get all subtopics from graph
                data = graph.get_topic_data(tid)
                all_subs = data.get("subtopics", [])
                if all_subs:
                    subtopic_text = ", ".join(all_subs[:3])  # Show first 3
            
            # Extract base topic name without part number
            topic_name = base_title.split(" (Part ")[0] if " (Part " in base_title else base_title
            
            # Build display title with subtopic instead of part number
            if subtopic_text:
                display_title = f"{topic_name}: {subtopic_text}"
            else:
                display_title = base_title  # Fallback to original with part number

            block += f"- {emoji} **{display_title}**  \n"
            block += f"  ⏱ {duration} min + {brk} min break  \n"
            block += f"  🔖 Topic: `{tid}`  \n\n"

    table_rows.append({"Day": day, "Sessions": block})

# ------------------------------------------------------
# Display Table (Full-width with improved formatting)
# ------------------------------------------------------
df = pd.DataFrame(table_rows)
st.markdown("### 📚 Weekly Plan (slot-wise)")
st.dataframe(
    df, 
    use_container_width=True, 
    hide_index=True,
    height=600,  # Taller table for better readability
    column_config={
        "Day": st.column_config.TextColumn(
            "Weekday",
            width="small",
            help="Day of the week"
        ),
        "Sessions": st.column_config.TextColumn(
            "Study Blocks",
            width="large",
            help="Your study sessions for the day"
        )
    }
)

# ------------------------------------------------------
# Insights (Multi-week aware)
# ------------------------------------------------------
valid_sessions = []
for week in range(1, weeks_available + 1):
    for d in WEEKDAYS:
        week_day_key = f"Week {week} - {d}"
        day_data = weekly_schedule.get(week_day_key, [])
        if isinstance(day_data, list):
            valid_sessions.extend(day_data)

session_len_default = user_data.get("session_length", 45)
sessions_count = len(valid_sessions)
total_minutes = sum(s.get("duration", session_len_default) for s in valid_sessions)
hours_count = total_minutes / 60
topics_count = len({s.get("topic_id") for s in valid_sessions if s.get("topic_id")})

st.markdown("---")
st.subheader("📊 Insights")

col1, col2, col3 = st.columns(3)
col1.metric("📘 Total Sessions", sessions_count)
col2.metric("⏱ Total Time", f"{hours_count:.1f}h")
col3.metric("📚 Unique Topics", topics_count)

# ------------------------------------------------------
# Export / Regenerate
# ------------------------------------------------------
st.markdown("---")
col1, col2 = st.columns([1, 3])

with col1:
    if st.button("📥 Export CSV"):
        csv = df.to_csv(index=False)
        st.download_button("Download", csv, "study_schedule.csv", "text/csv")

with col2:
    if st.button("🔄 Regenerate Schedule"):
        st.session_state.schedule_generated = False
        st.rerun()

# ============================================================
# EXPLAINABILITY - Natural Language Justification
# ============================================================
st.markdown("---")
st.subheader("🤖 AI Logic Explanation")
st.caption("Understand why the AI made these scheduling decisions")

if st.button("💬 Ask AI: Why this schedule?", type="primary"):
    with st.spinner("🧠 Analyzing scheduling constraints and logic..."):
        from backend.llm_helper import LLMHelper
        from backend.db import PersistenceManager
        
        pm_explain = PersistenceManager()
        
        # Prepare summary for LLM
        summary = (
            f"Total Sessions: {sessions_count}, "
            f"Total Time: {hours_count:.1f}h, "
            f"Unique Topics: {topics_count}"
        )
        
        # Describe logic used
        logic_description = (
            f"**Priority Calculation:**\n"
            f"- Deadline urgency (closer deadlines = higher priority)\n"
            f"- Topic weakness (your confidence ratings)\n"
            f"- Prerequisites (topics that unlock others)\n"
            f"- Difficulty matching peak hours\n\n"
            f"**Constraints Applied:**\n"
            f"- Study hours/day: {user_data.get('study_hours_per_day', 'N/A')}h\n"
            f"- Session length: {user_data.get('session_length', 'N/A')} min\n"
            f"- Peak hours: {', '.join(user_data.get('peak_hours', []))}\n"
            f"- Unavailable days: {len(user_data.get('unavailable_days', []))} day(s)"
        )
        
        llm = LLMHelper()
        explanation = llm.explain_schedule_logic(summary, logic_description)
        
        st.success(explanation)
        
        # Log this interaction
        pm_explain.log_event("Explainability", "User requested schedule justification", 
                           f"Topics: {topics_count}, Sessions: {sessions_count}")
        
        # Show detailed logic
        with st.expander("🔍 Detailed Scheduling Logic"):
            st.markdown(logic_description)
            
            # Show meta-reasoning if applied
            if st.session_state.get('original_path') and st.session_state.get('learning_path'):
                original = st.session_state.original_path
                current = st.session_state.learning_path
                
                if original != current:
                    from backend.meta_reasoner import MetaReasoner
                    meta = MetaReasoner(graph)
                    meta_explanation = meta.explain_reordering(original, current)
                    
                    st.markdown("---")
                    st.markdown(meta_explanation)
