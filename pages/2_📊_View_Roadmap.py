import streamlit as st
import networkx as nx
import plotly.graph_objects as go
from streamlit_agraph import agraph, Node, Edge, Config

st.set_page_config(page_title="View Roadmap", layout="wide")

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

st.title("📊 Learning Roadmap")

if not st.session_state.get('roadmap_generated', False):
    st.warning("⚠️ No roadmap generated yet. Please set your goal first!")
    st.info("👉 Go to **Set Goal** page to create your personalized learning roadmap.")
else:
    graph = st.session_state.graph
    learning_path = st.session_state.learning_path
    completed_topics = st.session_state.user_data.get('completed_topics', [])
    
    st.success(f"🎯 Goal: {st.session_state.user_data['goal']}")
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    total_topics = len(learning_path)
    completed = len(completed_topics)
    remaining = total_topics - completed
    
    total_hours = sum(graph.get_topic_data(t)['estimated_hours'] for t in learning_path)
    completed_hours = sum(graph.get_topic_data(t)['estimated_hours'] for t in completed_topics)
    
    with col1:
        st.metric("Total Topics", total_topics)
    
    with col2:
        st.metric("Completed", completed)
    
    with col3:
        st.metric("Remaining", remaining)
    
    with col4:
        st.metric("Total Hours", f"{total_hours}h")
    
    # Progress bar
    progress = (completed / total_topics * 100) if total_topics > 0 else 0
    st.progress(progress / 100)
    st.caption(f"Progress: {progress:.1f}%")
    
    st.markdown("---")
    
    # Learning path visualization
    st.subheader("📈 Optimal Learning Path (A* Algorithm)")
    
    st.info("💡 This path was calculated using **A* Search Algorithm** considering topic difficulty, prerequisites, and your deadline.")
    
    # Display learning path as ordered list
    for i, topic_id in enumerate(learning_path, 1):
        topic_data = graph.get_topic_data(topic_id)
        
        col1, col2, col3 = st.columns([0.5, 3, 1])
        
        with col1:
            if topic_id in completed_topics:
                st.markdown(f"✅ **{i}**")
            else:
                st.markdown(f"⭕ **{i}**")
        
        with col2:
            status = "✅ Completed" if topic_id in completed_topics else "🔓 Available"
            
            # Check if prerequisites are met
            prereqs = list(graph.graph.predecessors(topic_id))
            prereqs_met = all(p in completed_topics for p in prereqs)
            
            if not prereqs_met and topic_id not in completed_topics:
                status = "🔒 Locked"
            
            difficulty_emoji = "🟢" if topic_data['difficulty'] < 0.5 else "🟡" if topic_data['difficulty'] < 0.7 else "🔴"
            
            st.markdown(f"**{topic_data['title']}** {difficulty_emoji}")
            st.caption(f"{status} • {topic_data['category']} • {topic_data['estimated_hours']}h • Difficulty: {topic_data['difficulty']:.1f}")
        
        with col3:
            if topic_id not in completed_topics:
                if st.button("Mark Done", key=f"complete_{topic_id}"):
                    st.session_state.user_data['completed_topics'].append(topic_id)
                    st.rerun()
    
    st.markdown("---")
    
    # Graph visualization
    st.subheader("🕸️ Topic Dependency Graph")
    
    st.info("💡 **Interactive Graph:** Hover over nodes for details, drag to rearrange, click to select topics!")
    
    # 1. CONFIGURATION: Define how the graph looks and behaves
    config = Config(
        width=750,
        height=500,
        directed=True, 
        physics=True,           # ENABLE PHYSICS (Dynamic movement)
        hierarchical=False,     # Set to True if you want a strict Tree structure
        collapsible=False,
        nodeHighlightBehavior=True,
        highlightColor="#F7A242", # Orange highlight on hover
        # Physics settings to make it stabilize nicely
        physicsOptions={
            "barnesHut": {
                "gravitationalConstant": -3000,
                "centralGravity": 0.2,
                "springLength": 150,
                "springConstant": 0.02,
                "damping": 0.09,
                "avoidOverlap": 0.3
            },
            "minVelocity": 0.75,
            "solver": "barnesHut"
        }
    )

    # 2. DATA CONVERSION: NetworkX -> Agraph Nodes/Edges
    nodes = []
    edges = []

    completed_set = set(completed_topics)

    for topic_id in graph.graph.nodes:
        data = graph.get_topic_data(topic_id)
        
        # A. Determine Status & Color
        is_completed = topic_id in completed_set
        
        # Check prereqs
        prereqs = list(graph.graph.predecessors(topic_id))
        prereqs_met = all(p in completed_set for p in prereqs)
        
        if is_completed:
            color = "#00CC96"  # Green
            status_text = "✅ Completed"
        elif prereqs_met:
            color = "#636EFA"  # Blue (Available)
            status_text = "🔓 Available"
        else:
            color = "#FF6B6B"  # Red (Locked)
            status_text = "🔒 Locked"

        # B. Create Hover Text (Plain text for proper display)
        hover_text = (
            f"{data['title']}\n"
            f"Status: {status_text}\n"
            f"Time: {data['estimated_hours']}h | Difficulty: {data['difficulty']:.1f}\n"
            f"Category: {data.get('category', 'General')}"
        )

        # C. Create Node Object
        nodes.append(Node(
            id=topic_id,
            label=data['title'],     # Short label
            title=hover_text,        # <--- THIS IS THE HOVER DETAIL
            color=color,
            size=25 + (data['estimated_hours'] * 2), # Larger nodes for longer topics
            shape="dot",
            borderWidth=2,
            font={"color": "white" if not is_completed else "black"}
        ))

    for source, target in graph.graph.edges:
        edges.append(Edge(
            source=source,
            target=target,
            color="#888888",
            width=3,
            type="CURVE_SMOOTH", # Make lines curved
        ))

    # 3. RENDER THE GRAPH
    # The return value is the ID of the node clicked
    selected_node_id = agraph(nodes=nodes, edges=edges, config=config)

    # 4. HANDLE CLICK INTERACTION
    if selected_node_id:
        st.success(f"✨ You selected: **{graph.get_topic_data(selected_node_id)['title']}**")
        st.caption("👇 View full details in the 'Topic Details' section below")
    
    st.caption("🟢 Green = Completed • 🔵 Blue = Available • 🔴 Red = Locked (Prerequisites not met)")
    
    # Topic details
    st.markdown("---")
    st.subheader("📚 Topic Details")
    
    selected_topic = st.selectbox(
        "Select a topic to view details",
        learning_path,
        format_func=lambda x: graph.get_topic_data(x)['title']
    )
    
    if selected_topic:
        topic_data = graph.get_topic_data(selected_topic)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"### {topic_data['title']}")
            st.markdown(f"**Category:** {topic_data['category']}")
            st.markdown(f"**Estimated Time:** {topic_data['estimated_hours']} hours")
            st.markdown(f"**Difficulty:** {topic_data['difficulty']:.1f}/1.0")
            
            prereqs = list(graph.graph.predecessors(selected_topic))
            if prereqs:
                st.markdown("**Prerequisites:**")
                for prereq in prereqs:
                    prereq_data = graph.get_topic_data(prereq)
                    status = "✅" if prereq in completed_topics else "⭕"
                    st.markdown(f"- {status} {prereq_data['title']}")
            else:
                st.markdown("**Prerequisites:** None (Starting topic)")
        
        with col2:
            # Difficulty visualization
            difficulty = topic_data['difficulty']
            st.metric("Difficulty Level", f"{difficulty:.1%}")
            
            if difficulty < 0.5:
                st.success("🟢 Beginner Friendly")
            elif difficulty < 0.7:
                st.warning("🟡 Intermediate")
            else:
                st.error("🔴 Advanced")
