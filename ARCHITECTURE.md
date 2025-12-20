# 🏗️ System Architecture

## Overview

The Adaptive AI Study Planner is a **multi-agent AI system** that combines symbolic AI (search, reasoning), machine learning (LLM), and constraint satisfaction to create personalized learning plans.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Set Goal    │  │  Roadmap     │  │    Schedule View     │  │
│  │  (Input UI)  │  │  (Graph Viz) │  │  (Multi-week Tabs)   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                  │                      │              │
└─────────┼──────────────────┼──────────────────────┼──────────────┘
          │                  │                      │
          ↓                  ↓                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                     CONTROL LAYER                                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │             Streamlit Session State Manager                 │ │
│  │  - user_data, graph, learning_path, schedule                │ │
│  │  - roadmap_generated, schedule_generated flags              │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────┬────────────────────────────────────────┬───────────────┘
          │                                        │
          ↓                                        ↓
┌─────────────────────────┐         ┌──────────────────────────────┐
│   AI REASONING LAYER    │         │   CONSTRAINT SATISFACTION    │
│ ┌─────────────────────┐ │         │ ┌──────────────────────────┐ │
│ │  LLM Helper         │ │         │ │  CSP Scheduler           │ │
│ │  - Curriculum Gen   │ │         │ │  - Multi-week planning   │ │
│ │  - Explainability   │ │         │ │  - Session placement     │ │
│ └─────────┬───────────┘ │         │ │  - Slot capacity mgmt    │ │
│           ↓             │         │ └──────────────────────────┘ │
│ ┌─────────────────────┐ │         │                              │
│ │  Knowledge Graph    │ │         │ ┌──────────────────────────┐ │
│ │  - NetworkX DAG     │ │         │ │  Ethics Guard            │ │
│ │  - Priority calc    │ │         │ │  - Burnout prevention    │ │
│ │  - Dependencies     │ │         │ │  - Health constraints    │ │
│ └─────────┬───────────┘ │         │ └──────────────────────────┘ │
│           ↓             │         └──────────────────────────────┘
│ ┌─────────────────────┐ │
│ │  Reasoning Engine   │ │
│ │  - 5 priority rules │ │
│ │  - Explainable AI   │ │
│ └─────────┬───────────┘ │
│           ↓             │
│ ┌─────────────────────┐ │
│ │  A* Planner         │ │
│ │  - Optimal path     │ │
│ │  - Cost function    │ │
│ └─────────┬───────────┘ │
│           ↓             │
│ ┌─────────────────────┐ │
│ │  Meta-Reasoner      │ │
│ │  - Fatigue filter   │ │
│ │  - Strategic reorg  │ │
│ └─────────────────────┘ │
└─────────────────────────┘
          │
          ↓
┌─────────────────────────────────────────────────────────────────┐
│                   PERSISTENCE LAYER                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  PersistenceManager (SQLAlchemy + SQLite)                   │ │
│  │  - State serialization (Pickle)                             │ │
│  │  - Transparency logs (AgentLog table)                       │ │
│  │  - Session continuity                                       │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Layer Breakdown

### 1. Presentation Layer (Streamlit Pages)

**Technology:** Streamlit multi-page app

**Components:**

#### `1_🎯_Set_Goal.py` (Entry Point)
- **Purpose:** User input and validation
- **Features:**
  - Subject selection (templates + custom)
  - Timeline configuration (deadline, daily hours)
  - Session preferences (length, breaks, peak hours)
  - Availability matrix (unavailable days/slots)
  - Ethics validation (burnout check)
  - Intelligent loading state (shows AI steps)
  
**Data Flow:**
```python
User Input → Validation → Ethics Check → AI Pipeline → Session State
```

#### `2_📊_View_Roadmap.py` (Visualization)
- **Purpose:** Interactive dependency graph
- **Technology:** streamlit-agraph with Barnes-Hut physics
- **Features:**
  - Node coloring (Green/Blue/Red for status)
  - Smooth curved edges
  - Hover tooltips with topic details
  - Statistics dashboard (total topics, hours, completion %)

**Physics Configuration:**
```python
Config(
    gravitationalConstant=-3000,
    centralGravity=0.2,
    springLength=150,
    springConstant=0.02,
    avoidOverlap=0.3
)
```

#### `3_📅_View_Schedule.py` (Schedule Display)
- **Purpose:** Multi-week schedule presentation
- **Features:**
  - Week-based tabs (dynamic based on deadline)
  - Expandable day sections
  - Time slot grouping (6-9 AM, 9-12 PM, etc.)
  - Subtopic-based session titles
  - Full-width dataframe with column config
  - Insights panel (total sessions, hours, unique topics)

**Multi-Week Algorithm:**
```python
weeks_available = schedule.get("_weeks_available", 1)
for week in range(1, weeks_available + 1):
    for day in WEEKDAYS:
        sessions = schedule.get(f"Week {week} - {day}", [])
```

#### `4_📈_Progress.py` (Analytics)
- **Purpose:** Track completion and metrics
- **Features:**
  - Completion percentage
  - Time invested vs. remaining
  - Difficulty distribution charts
  - Deadline countdown

#### `5_⚙️_Settings.py` (Configuration)
- **Purpose:** API keys and system config
- **Features:**
  - Gemini API key management
  - Database reset option
  - Transparency logs viewer

---

### 2. Control Layer (Session Management)

**Technology:** Streamlit `st.session_state`

**State Variables:**
```python
{
    "user_data": {
        "subjects": List[str],
        "deadline": date,
        "study_hours_per_day": int,
        "session_length": int,
        "break_length": int,
        "peak_hours": List[str],
        "unavailable_slots": Dict[str, List[str]],
        "unavailable_days": List[str],
        "learning_style": str,
        "difficulty_preference": str,
        "completed_topics": List[str],
        "topic_weakness": Dict[str, float]
    },
    "graph": StudyGraph,
    "learning_path": List[str],
    "schedule": Dict[str, List[Dict]],
    "roadmap_generated": bool,
    "schedule_generated": bool
}
```

**Lifecycle:**
1. Initialize defaults on page load
2. Update on user actions
3. Persist to database after major operations
4. Restore from database on app restart

---

### 3. AI Reasoning Layer

#### **LLM Helper** (`llm_helper.py`)

**Purpose:** Interface with Google Gemini API for curriculum generation

**Capabilities:**
- Structured curriculum generation with subtopics
- JSON parsing with regex fallback
- Error handling with template fallback
- Natural language explanations for decisions

**Prompt Engineering:**
```python
prompt = f"""
You are an expert curriculum designer.
Generate a detailed curriculum for: {goal}

Return ONLY a JSON array with these fields:
{{
  "id": "unique_id",
  "title": "Topic Title",
  "prerequisites": ["id1", "id2"],
  "difficulty": 0.0 to 1.0,
  "category": "Category",
  "hours": 4,
  "description": "Summary",
  "subtopics": ["sub1", "sub2", "sub3"]
}}
"""
```

**Fallback Curriculum:**
When API unavailable, generates 3-topic template:
- Fundamentals (6h, difficulty 0.3)
- Core Concepts (8h, difficulty 0.5)
- Practice & Projects (10h, difficulty 0.6)

---

#### **Knowledge Graph** (`state_graph.py`)

**Purpose:** Active state space representation

**Technology:** NetworkX Directed Acyclic Graph (DAG)

**Node Attributes:**
```python
{
    "title": str,
    "prerequisites": List[str],
    "difficulty": float,
    "category": str,
    "estimated_hours": float,
    "description": str,
    "subtopics": List[str],
    "completed": bool,
    "priority": float  # Dynamically updated
}
```

**Key Methods:**
- `add_topic()` - Adds node with prerequisite edges
- `get_available_topics(completed)` - Returns topics with met prerequisites
- `recalculate_priorities(user_model)` - Invokes reasoning engine
- `get_learning_path()` - Topological sort for fallback ordering

**Active Knowledge:**
Graph updates its own priorities based on changing conditions (deadline, user progress).

---

#### **Reasoning Engine** (`reasoner.py`)

**Purpose:** Rule-based priority calculation

**Algorithm:**

```python
priority = 0.5  # Base

# Rule 1: Deadline Urgency
if days_remaining < 30:
    priority += 0.3 * (1 - days_remaining / 30)

# Rule 2: Difficulty Match
if "gradually" in learning_style:
    priority -= 0.2 * difficulty  # Easier first
elif "advanced" in learning_style:
    priority += 0.2 * difficulty  # Harder first

# Rule 3: Prerequisite Unlocking
dependents = graph.get_dependents(topic_id)
if len(dependents) > 2:
    priority += 0.2  # Critical path

# Rule 4: Spaced Repetition
if topic_id in completed_topics:
    priority += 0.15  # Review session

# Rule 5: Learning Style Match
if "hands-on" in style and "practice" in category:
    priority += 0.15

# Normalize to [0, 1]
priority = max(0.0, min(1.0, priority))
```

**Explainability:**
Each rule includes `explain_priority()` method that generates human-readable justification.

---

#### **A* Planner** (`a_star_planner.py`)

**Purpose:** Find optimal learning path

**Algorithm:** A* Search
- **State Space:** Powerset of topics (2^N states)
- **Initial State:** No topics completed
- **Goal State:** All topics completed
- **Actions:** Study an available topic (prerequisites met)

**Cost Function:**
```python
cost = time_required + (difficulty * 10) + ((1 - priority) * 5)
```

**Heuristic (Admissible):**
```python
h(state) = sum(estimated_hours for remaining topics)
```

**Priority Queue:**
```python
heapq.heappush(open_set, (
    f_score,    # g + h
    g_score,    # cost from start
    state,      # frozenset of completed topics
    path        # ordered list of topic IDs
))
```

**Guarantees:**
- Optimal path if prerequisites form DAG
- Polynomial time for sparse graphs
- Fallback to topological sort if search fails

---

#### **Meta-Reasoner** (`meta_reasoner.py`)

**Purpose:** Strategic transformation of A* output

**Concept:** "Thinking about thinking" - applies human factors

**Fatigue Filter Algorithm:**
```python
HARD_THRESHOLD = 0.6

reordered = []
for topic in ordered_topics:
    if previous_topic.difficulty >= HARD_THRESHOLD:
        # Last topic was hard - prefer easier next
        next_topic = select_easiest(available_topics)
    else:
        # Can handle hard topic now
        next_topic = select_hardest(available_topics)
    
    reordered.append(next_topic)
```

**Constraint Preservation:**
Only reorders when prerequisites allow. Never violates dependency graph.

**Output:**
- Reordered path with reduced cognitive load
- Explanation of each swap with difficulty values

---

### 4. Constraint Satisfaction Layer

#### **CSP Scheduler** (`scheduler.py`)

**Purpose:** Multi-week session scheduling with capacity constraints

**Algorithm:** Greedy CSP with multi-pass retry

**State:**
```python
schedule = {
    "Week 1 - Monday": [session1, session2],
    "Week 1 - Tuesday": [session3],
    # ...
    "Week N - Sunday": [sessionX]
}
```

**Constraints:**

1. **Slot Capacity:** 3 hours per slot (180 minutes)
```python
used_in_slot = sum(s["duration"] + s["break_after"] for s in slot_sessions)
remaining = 180 - used_in_slot
```

2. **Daily Study Limit:** User-defined max hours per day
```python
used_today = sum(s["duration"] + s["break_after"] for s in day_sessions)
remaining_today = daily_limit_minutes - used_today
```

3. **Sequential Parts:** Part N requires Part N-1 scheduled
```python
if part > 1 and (topic_id, part - 1) not in placed_parts:
    still_unplaced.append(session)  # Retry next pass
    continue
```

4. **Unavailable Slots:** Respect user's blocked times
```python
unavailable = user.unavailable_slots.get(day, [])
if slot in unavailable:
    continue
```

**Multi-Pass Algorithm:**

```python
for pass_num in range(max_passes):
    placed_in_this_pass = 0
    
    for session in unplaced_sessions:
        # Check prerequisites
        if prerequisites_not_met(session):
            still_unplaced.append(session)
            continue
        
        # Find best slot
        best_slot = find_best_slot(session)
        
        if best_slot:
            place_session(best_slot, session)
            placed_in_this_pass += 1
        else:
            still_unplaced.append(session)
    
    # Stop if no progress
    if placed_in_this_pass == 0:
        break
```

**Scoring Function:**
```python
score = 0

# Prefer peak hours for difficult topics
if is_peak_hour and difficulty > 0.6:
    score += 50

# Prefer earlier slots for high priority
if priority > 0.7:
    score += 30 * (6 - slot_index)

# Prefer filling early weeks
score -= week_number * 10

# Capacity utilization bonus
score += (remaining_capacity / total_capacity) * 20

return score
```

**Output:**
```python
{
    "Week 1 - Monday": [...],
    # ... all weeks ...
    "_weeks_available": 6,
    "_current_week_schedule": {...},  # Week 1 for backward compatibility
    "_dropped_topics": [...],
    "_dropped_parts": [...]
}
```

---

#### **Ethics Guard** (`ethics.py`)

**Purpose:** Enforce well-being constraints

**Research Foundation:**
- Ericsson et al. (1993) - Deliberate Practice
- Sweller (1988) - Cognitive Load Theory
- Walker (2017) - Sleep and Learning

**Constraints:**

```python
MAX_DAILY_HOURS = 6       # Hard limit
OPTIMAL_DAILY_HOURS = 4   # Recommended
MIN_BREAK_RATIO = 0.15    # 15% minimum breaks
LATE_NIGHT_CUTOFF = 23    # No studying past 11 PM
MIN_REST_DAYS = 1         # Per week
```

**Validation Logic:**

```python
def check_health_constraints(user_model):
    errors = []
    warnings = []
    
    # Burnout check
    if daily_hours > MAX_DAILY_HOURS:
        errors.append("CRITICAL: Burnout risk - refuses to proceed")
    
    # Break adequacy
    ratio = break_min / (session_min + break_min)
    if ratio < MIN_BREAK_RATIO:
        warnings.append("Insufficient breaks - fatigue risk")
    
    # Rest day check
    if len(unavailable_days) == 0:
        warnings.append("No rest days - recommend at least 1/week")
    
    # Late night study
    if any(slot.ends_after(LATE_NIGHT_CUTOFF) for slot in peak_hours):
        warnings.append("Late night study disrupts sleep")
    
    is_safe = len(errors) == 0
    return is_safe, errors + warnings
```

**Refusal Mechanism:**

If `is_safe = False`, the system:
1. Shows error message with research citations
2. Explains health risks
3. Suggests healthier alternative configuration
4. **Refuses to generate schedule** (ethical constraint)

---

### 5. Persistence Layer

#### **Database Schema** (`db.py`)

**Technology:** SQLAlchemy ORM + SQLite

**Tables:**

1. **StateStore** - Complex object serialization
```python
class StateStore(Base):
    __tablename__ = 'state_store'
    
    key = Column(String, primary_key=True)      # "graph", "user_data"
    value = Column(PickleType)                   # Serialized object
    timestamp = Column(DateTime)
```

2. **AgentLog** - Transparency logging
```python
class AgentLog(Base):
    __tablename__ = 'agent_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    module = Column(String)     # "Reasoning", "A*", "CSP"
    message = Column(Text)
    details = Column(Text)      # JSON serialized
```

3. **TopicDB** - Topic metadata (legacy)
```python
class TopicDB(Base):
    __tablename__ = 'topics'
    
    id = Column(String, primary_key=True)
    title = Column(String)
    prerequisites = Column(PickleType)
    difficulty = Column(Float)
    completed = Column(Boolean)
```

**PersistenceManager API:**

```python
pm = PersistenceManager()

# Save complex objects
pm.save_state('graph', graph_object)
pm.save_state('user_data', user_dict)

# Load state
graph = pm.load_state('graph')

# Transparency logging
pm.log_event("CSP", "Scheduled 15 sessions", "0 dropped topics")

# Retrieve logs
logs = pm.get_recent_logs(limit=10)
```

---

## Data Flow: Complete Pipeline

### Stage 1: User Input
```
User → Set Goal Page
  ↓
  Validate Input
  ↓
  Ethics Check (burnout prevention)
  ↓
  Store in session_state.user_data
```

### Stage 2: Curriculum Generation
```
session_state.user_data
  ↓
  LLM Helper.generate_curriculum(goal)
  ↓
  Gemini API (with fallback to templates)
  ↓
  JSON curriculum with subtopics
```

### Stage 3: Knowledge Graph Construction
```
Curriculum List
  ↓
  StudyGraph.add_topic() for each
  ↓
  NetworkX DAG with prerequisites
  ↓
  Store in session_state.graph
```

### Stage 4: Priority Calculation
```
graph + user_model
  ↓
  ReasoningEngine.apply_reasoning()
  ↓
  5 rules calculate priorities
  ↓
  graph.update_priority() for each topic
```

### Stage 5: Optimal Path Finding
```
graph + user_model
  ↓
  AStarPlanner.find_optimal_path()
  ↓
  A* search with cost function
  ↓
  Ordered list of topics
```

### Stage 6: Meta-Reasoning
```
optimal_path from A*
  ↓
  MetaReasoner.apply_fatigue_filter()
  ↓
  Reorder to prevent Hard→Hard sequences
  ↓
  Store in session_state.learning_path
```

### Stage 7: Multi-Week Scheduling
```
learning_path + user_data
  ↓
  SchedulerCSP.generate_schedule()
  ↓
  Multi-pass CSP placement
  ↓
  {Week N - Day: [sessions]}
  ↓
  Store in session_state.schedule
```

### Stage 8: Persistence
```
All session_state data
  ↓
  PersistenceManager.save_state()
  ↓
  Pickle serialization
  ↓
  SQLite database
```

### Stage 9: Visualization
```
session_state.graph
  ↓
  View Roadmap Page
  ↓
  streamlit-agraph rendering
  ↓
  Interactive physics-based graph
```

```
session_state.schedule
  ↓
  View Schedule Page
  ↓
  Multi-week tabs with expandable days
  ↓
  Subtopic-based session display
```

---

## Technology Stack

### Core
- **Python 3.8+**
- **Streamlit 1.28+** - Web framework
- **NetworkX 3.0+** - Graph algorithms

### AI/ML
- **Google Generative AI (Gemini)** - LLM for curriculum
- **Custom A* implementation** - Pathfinding
- **Rule-based reasoner** - Priority calculation

### Data
- **SQLAlchemy 2.0+** - ORM
- **SQLite** - Database
- **Pickle** - Object serialization

### Visualization
- **streamlit-agraph** - Interactive graphs
- **Plotly** - Charts and analytics
- **Pandas** - Data manipulation

### Algorithms
- **A* Search** - Optimal pathfinding
- **CSP (Constraint Satisfaction)** - Scheduling
- **Topological Sort** - Dependency resolution
- **Greedy algorithms** - Slot assignment
- **Rule-based reasoning** - Priority calculation

---

## Performance Characteristics

### Time Complexity

| Component | Complexity | Notes |
|-----------|-----------|-------|
| LLM Generation | O(1) | API call, fixed time |
| Graph Construction | O(V + E) | V = topics, E = prerequisites |
| Reasoning Engine | O(V) | Linear scan with rule application |
| A* Search | O(b^d) | Worst case, typically faster |
| Meta-Reasoner | O(V) | Single pass reordering |
| CSP Scheduler | O(P × W × D × S) | P=parts, W=weeks, D=days, S=slots |

**CSP Scheduler Optimization:**
- Multi-pass: O(10 × P × W × D × S) worst case
- Early termination when no progress
- Typically 2-3 passes needed

### Space Complexity

| Component | Complexity | Notes |
|-----------|-----------|-------|
| Knowledge Graph | O(V + E) | Nodes + edges |
| A* Open Set | O(2^V) | Worst case state space |
| Schedule | O(W × D × S) | Week-day-slot sessions |
| Database | O(V + L) | Topics + logs |

### Scalability Limits

- **Topics:** Tested up to 50 topics (graph remains manageable)
- **Study Period:** Up to 26 weeks (6 months) without performance issues
- **Sessions:** 500+ sessions scheduled without lag
- **Database:** Logs auto-cleanup after 30 days

---

## Security & Privacy

### Data Storage
- **Local SQLite database** - No cloud uploads
- **No personal data sent to APIs** (only subject names)
- **API keys stored in .env** (not in code)

### LLM Privacy
- Curriculum generation sends only: goal string
- No schedule, preferences, or personal info to Gemini
- Fallback templates when API disabled

### Session Security
- Streamlit session state (server-side)
- No client-side storage
- Database access restricted to local filesystem

---

## Error Handling

### LLM Failures
```python
try:
    curriculum = llm.generate_curriculum(goal)
except Exception as e:
    print("LLM failed:", e)
    curriculum = fallback_curriculum(goal)
```

### A* Search Failures
```python
path = planner.find_optimal_path()
if not path:
    # Fallback to topological sort
    path = graph.get_learning_path()
```

### CSP Scheduling Failures
```python
if all topics dropped:
    show_root_cause_analysis()
    suggest_solutions()
    # Options: extend deadline, add slots, reduce hours
```

### Database Errors
```python
try:
    pm.save_state('key', obj)
except Exception as e:
    print("Persistence failed:", e)
    # Continue without saving (graceful degradation)
```

---

## Extension Points

### Adding New Reasoning Rules
```python
# In reasoner.py
def _custom_rule(self, topic_data, user_model) -> float:
    # Your logic here
    return priority_boost

# In apply_reasoning()
priority += self._custom_rule(topic_data, user_model)
```

### Custom Scheduling Constraints
```python
# In scheduler.py
def _custom_constraint(self, session, day, slot) -> bool:
    # Your constraint logic
    return is_allowed

# In placement loop
if not self._custom_constraint(session, day, slot):
    continue
```

### New Visualization Pages
```python
# Create pages/6_📊_New_Page.py
import streamlit as st

st.set_page_config(page_title="New Feature")
# Sidebar progress (copy from other pages)
# Your custom logic here
```

---

## Deployment Options

### Local Development
```bash
streamlit run pages/1_🎯_Set_Goal.py
```

### Streamlit Cloud
1. Push to GitHub
2. Connect repository to Streamlit Cloud
3. Set environment variables (GEMINI_API_KEY)
4. Deploy

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "pages/1_🎯_Set_Goal.py"]
```

### Production Considerations
- Use PostgreSQL instead of SQLite for multi-user
- Add authentication layer
- Enable HTTPS
- Implement rate limiting for LLM calls
- Add monitoring and logging

---

**Architecture designed for modularity, extensibility, and ethical AI principles.**
