# test_scheduler.py

import json
from datetime import datetime, timedelta
from backend.state_graph import StudyGraph
from backend.user_model import UserModel
from backend.a_star_planner import AStarPlanner
from backend.reasoner import ReasoningEngine
from backend.scheduler import SchedulerCSP

print("\n=== TEST: HYBRID CSP SCHEDULER (Option 3) ===")

# -----------------------------
# 1. BUILD SAMPLE GRAPH
# -----------------------------
graph = StudyGraph()

graph.add_topic(
    topic_id="t1",
    title="Introduction to Python",
    prerequisites=[],
    difficulty=0.2,
    category="Basics",
    estimated_hours=2
)

graph.add_topic(
    topic_id="t2",
    title="Modules & Packages",
    prerequisites=["t1"],
    difficulty=0.4,
    category="Programming",
    estimated_hours=4
)

graph.add_topic(
    topic_id="t3",
    title="Object Oriented Programming",
    prerequisites=["t2"],
    difficulty=0.7,
    category="Advanced",
    estimated_hours=5
)

graph.add_topic(
    topic_id="t4",
    title="Working with External Libraries",
    prerequisites=["t2"],
    difficulty=0.6,
    category="Programming",
    estimated_hours=3
)

# -----------------------------
# 2. USER MODEL
# -----------------------------
user = UserModel(
    goal="Learn Python",
    deadline=datetime.now() + timedelta(days=25),
    study_hours_per_day=3,        # 180 min/day
    session_length=45,            # 45 min each session
    break_length=10,
    peak_hours=["9-12 PM", "6-9 PM"],  # user's high-focus hours
    unavailable_days=["Sunday"],
    learning_style="Mixed",
    difficulty_preference="Balanced progression",
    completed_topics=[],          # none completed
    topic_weakness={
        "t3": 0.9,  # OOP is hard for user
        "t4": 0.3
    },
    priority_weights={
        "prerequisites": 1.0,
        "deadline": 0.8,
        "difficulty": 0.7,
        "weakness": 0.6
    }
)

# -----------------------------
# 3. APPLY REASONING ENGINE
# -----------------------------
reasoner = ReasoningEngine()
priorities = reasoner.apply_reasoning(graph, user)
print("\n=== Topic Priorities ===")
for tid, pr in priorities.items():
    print(f"{tid}: {pr:.2f}")

# -----------------------------
# 4. A* TO GET ORDERED TOPICS
# -----------------------------
planner = AStarPlanner(graph, user)
learning_path = planner.find_optimal_path()

print("\n=== A* Optimal Learning Path ===")
print(learning_path)

# -----------------------------
# 5. RUN CSP SCHEDULER
# -----------------------------
scheduler = SchedulerCSP(graph, user, learning_path)
schedule = scheduler.generate_schedule()

# -----------------------------
# 6. SAVE OUTPUT TO JSON
# -----------------------------
with open("scheduler_output.json", "w") as f:
    json.dump(schedule, f, indent=4)

print("\n⭐⭐ SCHEDULE GENERATED SUCCESSFULLY! ⭐⭐")
print("Output saved to scheduler_output.json\n")
