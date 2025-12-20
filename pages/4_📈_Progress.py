import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Progress Tracking", layout="wide")

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

st.title("📈 Progress Tracking")

if not st.session_state.get('roadmap_generated', False):
    st.warning("⚠️ No roadmap generated yet. Please set your goal first!")
    st.info("👉 Go to **Set Goal** page to create your personalized learning roadmap.")
else:
    graph = st.session_state.graph
    learning_path = st.session_state.learning_path
    completed_topics = st.session_state.user_data.get('completed_topics', [])
    user_data = st.session_state.user_data
    
    # Overall progress
    st.subheader("🎯 Overall Progress")
    
    total_topics = len(learning_path)
    completed = len(completed_topics)
    progress_pct = (completed / total_topics * 100) if total_topics > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Completion", f"{progress_pct:.1f}%", f"{completed}/{total_topics} topics")
    
    with col2:
        total_hours = sum(graph.get_topic_data(t)['estimated_hours'] for t in learning_path)
        completed_hours = sum(graph.get_topic_data(t)['estimated_hours'] for t in completed_topics)
        st.metric("Hours Completed", f"{completed_hours}h", f"of {total_hours}h")
    
    with col3:
        days_left = (user_data['deadline'] - datetime.now().date()).days
        st.metric("Days Remaining", days_left)
    
    with col4:
        remaining_hours = total_hours - completed_hours
        hours_per_day = remaining_hours / days_left if days_left > 0 else 0
        st.metric("Required Daily", f"{hours_per_day:.1f}h")
    
    # Progress bar
    st.progress(progress_pct / 100)
    
    # Check if on track
    st.markdown("---")
    
    if progress_pct >= 50:  # Simple check: if completed more than half
        st.success(f"✅ You're on track! Keep up the great work!")
    else:
        st.warning(f"⚠️ You're behind schedule. Try to increase daily study time.")
    
    # Category breakdown
    st.markdown("---")
    st.subheader("📊 Progress by Category")
    
    # Group topics by category
    categories = {}
    for topic_id in learning_path:
        topic_data = graph.get_topic_data(topic_id)
        category = topic_data['category']
        
        if category not in categories:
            categories[category] = {'total': 0, 'completed': 0}
        
        categories[category]['total'] += 1
        if topic_id in completed_topics:
            categories[category]['completed'] += 1
    
    # Create bar chart
    category_names = list(categories.keys())
    completed_counts = [categories[c]['completed'] for c in category_names]
    total_counts = [categories[c]['total'] for c in category_names]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Completed',
        x=category_names,
        y=completed_counts,
        marker_color='lightgreen'
    ))
    fig.add_trace(go.Bar(
        name='Remaining',
        x=category_names,
        y=[t - c for t, c in zip(total_counts, completed_counts)],
        marker_color='lightcoral'
    ))
    
    fig.update_layout(
        barmode='stack',
        title='Topics by Category',
        xaxis_title='Category',
        yaxis_title='Number of Topics',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Difficulty breakdown
    st.markdown("---")
    st.subheader("📊 Progress by Difficulty")
    
    difficulty_ranges = {
        'Easy (0-0.5)': (0, 0.5),
        'Medium (0.5-0.7)': (0.5, 0.7),
        'Hard (0.7-1.0)': (0.7, 1.0)
    }
    
    diff_stats = {k: {'total': 0, 'completed': 0} for k in difficulty_ranges.keys()}
    
    for topic_id in learning_path:
        topic_data = graph.get_topic_data(topic_id)
        difficulty = topic_data['difficulty']
        
        for label, (min_d, max_d) in difficulty_ranges.items():
            if min_d <= difficulty < max_d or (label == 'Hard (0.7-1.0)' and difficulty == 1.0):
                diff_stats[label]['total'] += 1
                if topic_id in completed_topics:
                    diff_stats[label]['completed'] += 1
                break
    
    col1, col2, col3 = st.columns(3)
    
    for i, (label, stats) in enumerate(diff_stats.items()):
        with [col1, col2, col3][i]:
            pct = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            st.metric(label, f"{pct:.0f}%", f"{stats['completed']}/{stats['total']}")
    
    # Recent activity
    st.markdown("---")
    st.subheader("🔥 Recent Activity")
    
    if completed_topics:
        st.success(f"✅ You've completed {len(completed_topics)} topics!")
        
        with st.expander("View completed topics"):
            for topic_id in completed_topics:
                topic_data = graph.get_topic_data(topic_id)
                st.markdown(f"- ✅ **{topic_data['title']}** ({topic_data['category']})")
    else:
        st.info("No topics completed yet. Start your learning journey!")
    
    # Upcoming topics
    st.markdown("---")
    st.subheader("🎯 Next Steps")
    
    available_topics = graph.get_available_topics(completed_topics)
    
    if available_topics:
        st.markdown("**Topics you can start now:**")
        
        for topic_id in available_topics[:5]:
            topic_data = graph.get_topic_data(topic_id)
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                difficulty_emoji = "🟢" if topic_data['difficulty'] < 0.5 else "🟡" if topic_data['difficulty'] < 0.7 else "🔴"
                st.markdown(f"{difficulty_emoji} **{topic_data['title']}**")
            
            with col2:
                st.caption(f"{topic_data['estimated_hours']}h")
            
            with col3:
                if st.button("Start", key=f"start_{topic_id}"):
                    st.info(f"Starting {topic_data['title']}...")
    else:
        if len(completed_topics) == len(learning_path):
            st.success("🎉 Congratulations! You've completed all topics!")
            st.balloons()
        else:
            st.warning("Complete prerequisites to unlock more topics.")
    
    # Adaptive feedback
    st.markdown("---")
    st.subheader("💬 Feedback & Adaptation")
    
    with st.form("feedback_form"):
        st.markdown("Help AI adapt to your learning style:")
        
        selected_topic = st.selectbox(
            "Select a completed topic to rate",
            [t for t in completed_topics],
            format_func=lambda x: graph.get_topic_data(x)['title'] if x else ""
        ) if completed_topics else None
        
        if selected_topic:
            difficulty_rating = st.slider(
                "How difficult was this topic for you?",
                min_value=1,
                max_value=10,
                value=5,
                help="1 = Very Easy, 10 = Very Hard"
            )
            
            time_rating = st.radio(
                "Time estimation accuracy:",
                ["Took less time", "About right", "Took more time"]
            )
            
        if st.form_submit_button("Submit Feedback"):
            st.success("✅ Feedback recorded! AI will adjust future recommendations.")
            
            # ✅ AGENTIC BEHAVIOR: Auto-trigger re-planning based on feedback
            # This makes it a true "Agent" not just a "Tool"
            
            # Update user model with feedback
            if time_rating == "Took more time":
                # User is slower than estimated - increase future time estimates
                effectiveness_penalty = 0.8  # They're 20% slower
                st.session_state.user_data['avg_session_effectiveness'] = effectiveness_penalty
                
                st.info("🤖 **Agent Action**: Detected you need more time. "
                       "Automatically adjusting future schedules to give you 25% more time per topic.")
                
            elif time_rating == "Took less time":
                # User is faster - can be more ambitious
                effectiveness_boost = 1.2
                st.session_state.user_data['avg_session_effectiveness'] = effectiveness_boost
                
                st.info("🤖 **Agent Action**: You're ahead of schedule! "
                       "I can add more challenging topics to your plan.")
            
            # Update weakness scores
            normalized_difficulty = difficulty_rating / 10.0
            if selected_topic in st.session_state.user_data.get('topic_weakness', {}):
                # Update weakness based on actual difficulty experienced
                current_weakness = st.session_state.user_data['topic_weakness'][selected_topic]
                # Blend old and new: 70% new, 30% old
                new_weakness = 0.7 * normalized_difficulty + 0.3 * current_weakness
                st.session_state.user_data['topic_weakness'][selected_topic] = new_weakness
            
            # AUTO-REPLAN: Trigger re-calculation without user clicking anything
            if st.session_state.get('graph') and st.session_state.get('learning_path'):
                st.warning("🔄 **Autonomous Re-planning Triggered**...")
                
                try:
                    from backend.user_model import UserModel
                    from backend.a_star_planner import AStarPlanner
                    from backend.meta_reasoner import MetaReasoner
                    
                    # Rebuild user model with updated data
                    user_model = UserModel(**st.session_state.user_data)
                    
                    # Recalculate priorities based on new feedback
                    graph = st.session_state.graph
                    graph.recalculate_priorities(user_model)
                    
                    # Re-run A* with new priorities
                    planner = AStarPlanner(graph, user_model)
                    new_path = planner.find_optimal_path()
                    
                    # Apply meta-reasoning
                    meta = MetaReasoner(graph)
                    new_path = meta.apply_fatigue_filter(new_path)
                    
                    # Update session state
                    st.session_state.learning_path = new_path
                    st.session_state.schedule_generated = False  # Force re-schedule
                    
                    st.success("✅ **Your learning path has been automatically updated!**")
                    st.info("💡 Go to **View Schedule** to see your optimized plan.")
                    
                except Exception as e:
                    st.error(f"Auto-replan failed: {e}")
                    st.caption("Don't worry - your feedback is still saved.")