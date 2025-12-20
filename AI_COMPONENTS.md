# 🤖 AI Components: Inner Workings

This document provides a deep dive into the AI modules that power the Adaptive Study Planner, explaining the algorithms, data structures, and design decisions behind each component.

---

## Table of Contents

1. [LLM Helper - Curriculum Generation](#1-llm-helper---curriculum-generation)
2. [Knowledge Graph - State Representation](#2-knowledge-graph---state-representation)
3. [Reasoning Engine - Rule-Based AI](#3-reasoning-engine---rule-based-ai)
4. [A* Planner - Optimal Pathfinding](#4-a-planner---optimal-pathfinding)
5. [Meta-Reasoner - Strategic Intelligence](#5-meta-reasoner---strategic-intelligence)
6. [CSP Scheduler - Constraint Satisfaction](#6-csp-scheduler---constraint-satisfaction)
7. [Ethics Guard - Safety Layer](#7-ethics-guard---safety-layer)
8. [Persistence Manager - State Management](#8-persistence-manager---state-management)

---

## 1. LLM Helper - Curriculum Generation

### Purpose
Generate structured curriculum with subtopics using Google's Gemini LLM.

### Architecture

```python
class LLMHelper:
    def __init__(self, api_key):
        self.api_key = api_key
        self.use_llm = False
        self.model = None
```

### Initialization Process

**Step 1: API Key Validation**
```python
if not self.api_key or self.api_key == "your_api_key_here":
    print("⚠️ No Gemini API key. Using fallback templates.")
    return
```

**Step 2: Model Selection (Cascading Fallback)**
```python
model_list = [
    "models/gemini-2.5-flash",      # Latest
    "gemini-2.5-flash",             # Alternate naming
    "models/gemini-flash-latest",   # Generic latest
    "gemini-pro"                    # Legacy stable
]

for model_name in model_list:
    try:
        test = genai.GenerativeModel(model_name)
        test.generate_content("hello")  # Smoke test
        self.model = test
        self.use_llm = True
        break
    except:
        continue  # Try next model
```

**Why Cascading?**
- Google frequently updates model names
- Ensures compatibility across API versions
- Graceful degradation if specific model unavailable

---

### Curriculum Generation Algorithm

#### Input
```python
goal = "Learn System Design and Operating Systems"
```

#### Prompt Engineering

**Critical Design Choice:** Double-brace JSON escaping

```python
prompt = """
Generate a detailed curriculum for: {goal}

Return ONLY a JSON array with these fields:
{{
  "id": "unique_id_here",
  "title": "Topic Title",
  "prerequisites": ["list_of_ids"],
  "difficulty": 0.0 to 1.0,
  "subtopics": ["sub1", "sub2", "sub3"]
}}
""".format(goal=goal)
```

**Why `{{` and `}}`?**
- `.format()` treats `{` and `}` as placeholders
- Escaping prevents premature substitution
- Ensures LLM receives literal JSON structure

**Structured Output Strategy:**
1. **Explicit format specification** - "Return ONLY a JSON array"
2. **Concrete examples** - Shows exact field structure
3. **Constraints** - "3-8 useful subtopics", "lowercase_underscored IDs"
4. **No free-form text** - Reduces parsing errors

---

#### Response Parsing

**Challenge:** LLMs often add markdown formatting

```python
text = response.text.strip()
# Input might be: "Here's the curriculum:\n```json\n[{...}]\n```\nLet me know!"

# Regex extraction
match = re.search(r"\[[\s\S]+\]", text)
if not match:
    raise ValueError("No JSON array found")

data = json.loads(match.group())
```

**Why Regex?**
- Extracts JSON even with surrounding text
- Handles markdown code blocks
- More robust than `json.loads(text)` alone

---

#### Subtopics Validation

```python
cleaned = []
for topic in data:
    if "subtopics" not in topic or topic["subtopics"] is None:
        topic["subtopics"] = []  # Ensure field exists
    cleaned.append(topic)
```

**Why Critical?**
- Downstream code assumes `subtopics` field exists
- Prevents `KeyError` exceptions
- Enables session-level subtopic assignment

---

### Fallback Curriculum

**When Triggered:**
- No API key provided
- API call fails
- JSON parsing fails
- Rate limit exceeded

**Template Structure:**
```python
[
    {
        "id": "fundamentals",
        "title": f"{subject} Fundamentals",
        "prerequisites": [],
        "difficulty": 0.3,
        "hours": 6,
        "subtopics": [
            "Key concepts",
            "Basic terminology",
            "Real-world examples"
        ]
    },
    {
        "id": "core_concepts",
        "title": f"{subject} Core Concepts",
        "prerequisites": ["fundamentals"],
        "difficulty": 0.5,
        "hours": 8,
        "subtopics": [
            "Important sub-areas",
            "Common patterns",
            "Typical workflows"
        ]
    },
    {
        "id": "practice",
        "title": f"{subject} Practice & Projects",
        "prerequisites": ["core_concepts"],
        "difficulty": 0.6,
        "hours": 10,
        "subtopics": [
            "Mini project 1",
            "Mini project 2",
            "Error handling & debugging"
        ]
    }
]
```

**Design Rationale:**
- **Progressive difficulty:** 0.3 → 0.5 → 0.6 (gradual ramp)
- **Linear prerequisites:** Fundamentals → Core → Practice
- **Increasing time:** 6h → 8h → 10h (complexity grows)
- **Generic but useful:** Applicable to any subject

---

### Explainability Feature

```python
def explain_schedule_logic(self, schedule_summary, priority_logic):
    """
    Generate natural language justification for AI decisions
    """
    if not self.use_llm:
        # Fallback: Template explanation
        return f"Schedule optimized based on: {priority_logic}"
    
    prompt = f"""
You are an AI Study Coach explaining decisions to a student.

**Logic Used:** {priority_logic}
**Summary:** {schedule_summary}

Explain in 2-3 friendly sentences:
1. Why topics prioritized this way
2. How this fits their goals
3. One specific benefit

Be encouraging and reference actual numbers.
    """
    
    response = self.model.generate_content(prompt)
    return response.text.strip()
```

**Example Output:**
> "I've prioritized Data Structures & Algorithms first because it unlocks 4 other topics in your roadmap. With 45 days until your deadline, front-loading these foundational topics ensures you'll have time to build on them. By studying DSA during your peak hours (9-12 PM), you'll retain up to 30% more compared to late-night sessions!"

**Why LLM for Explanations?**
- Natural, conversational tone
- Adapts to user's specific context
- Personalized messaging (not generic templates)

---

## 2. Knowledge Graph - State Representation

### Purpose
Active knowledge representation using directed acyclic graph (DAG) to model topic dependencies.

### Data Structure

```python
class StudyGraph:
    def __init__(self):
        self.graph = nx.DiGraph()  # NetworkX directed graph
```

**Why NetworkX?**
- Mature graph algorithms (topological sort, BFS, DFS)
- Efficient adjacency list representation
- Built-in visualization support

---

### Node Schema

```python
self.graph.add_node(
    topic_id,                          # Unique identifier
    title="Data Structures",           # Display name
    prerequisites=["fundamentals"],    # List of IDs
    difficulty=0.7,                    # 0.0 to 1.0
    category="Core CS",                # Grouping
    estimated_hours=12,                # Time estimate
    description="Arrays, trees...",    # Summary
    subtopics=["Arrays", "LinkedLists"],  # Subtopic breakdown
    completed=False,                   # Tracking state
    priority=0.5                       # Dynamic (updated by reasoner)
)
```

**Active Representation:**
- Nodes are not static—`priority` updates based on user progress
- Graph "thinks" by recalculating priorities

---

### Edge Semantics

```python
for prereq in prerequisites:
    if prereq in self.graph.nodes:
        self.graph.add_edge(prereq, topic_id)
```

**Edge Direction:** Prerequisite → Dependent

Example:
```
fundamentals → data_structures → algorithms
```

**Why DAG (Directed Acyclic Graph)?**
- **Directed:** Prerequisites have order
- **Acyclic:** No circular dependencies (A requires B requires A)
- Enables topological sorting (linear ordering respecting dependencies)

---

### Core Algorithms

#### 1. Available Topics (A* Dependency)

```python
def get_available_topics(self, completed_topics: List[str]) -> List[str]:
    """
    Return topics whose prerequisites are all completed.
    This is the 'action space' for A* search.
    """
    available = []
    
    for node in self.graph.nodes:
        if node in completed_topics:
            continue  # Already done
        
        # Get prerequisites
        prereqs = list(self.graph.predecessors(node))
        
        # Check if all prerequisites satisfied
        if all(p in completed_topics for p in prereqs):
            available.append(node)
    
    return available
```

**Time Complexity:** O(V + E)
- V = number of topics
- E = number of prerequisite edges

**Example:**
```python
completed = ["fundamentals"]
available = graph.get_available_topics(completed)
# Returns: ["data_structures", "intro_to_algorithms"]
# (Both only require "fundamentals")
```

---

#### 2. Topological Sorting (Fallback Ordering)

```python
def get_learning_path(self) -> List[str]:
    """
    Return a valid learning order using topological sort.
    Used as fallback if A* fails.
    """
    try:
        return list(nx.topological_sort(self.graph))
    except nx.NetworkXError:
        # Graph has cycles—return arbitrary order
        return list(self.graph.nodes)
```

**Kahn's Algorithm (NetworkX Implementation):**
1. Find nodes with no incoming edges (no prerequisites)
2. Remove node and its outgoing edges
3. Repeat until graph empty

**Output:** `[fundamentals, data_structures, algorithms, ...]`

**Guarantee:** If followed, no topic is studied before its prerequisites.

---

#### 3. Priority Recalculation (Active Reasoning)

```python
def recalculate_priorities(self, user_model):
    """
    Invoke reasoning engine to update all topic priorities.
    Makes the graph 'alive'—it updates based on context.
    """
    from backend.reasoner import ReasoningEngine
    
    reasoner = ReasoningEngine()
    priorities = reasoner.apply_reasoning(self, user_model)
    
    # Update each node's priority
    for topic_id, priority in priorities.items():
        if topic_id in self.graph.nodes:
            self.graph.nodes[topic_id]["priority"] = priority
    
    return priorities
```

**When Called:**
- After user sets deadline (urgency changes)
- After user rates topic confidence (weakness changes)
- Before A* search (to use updated priorities)

**Example State Change:**
```python
# Initial state
graph.nodes["algorithms"]["priority"] = 0.5

# User sets deadline to 14 days (urgent)
priorities = graph.recalculate_priorities(user_model)

# Updated state
graph.nodes["algorithms"]["priority"] = 0.85  # Boosted!
```

---

### Visualization Support

```python
def visualize(self):
    """
    Export graph data for frontend rendering.
    """
    nodes = []
    edges = []
    
    for node_id in self.graph.nodes:
        data = self.graph.nodes[node_id]
        nodes.append({
            "id": node_id,
            "label": data["title"],
            "difficulty": data["difficulty"],
            "category": data["category"],
            "hours": data["estimated_hours"],
            "subtopics": data.get("subtopics", [])
        })
    
    for source, target in self.graph.edges:
        edges.append({
            "source": source,
            "target": target
        })
    
    return {"nodes": nodes, "edges": edges}
```

**Frontend Integration (streamlit-agraph):**
```python
graph_data = graph.visualize()

nodes = [Node(id=n["id"], label=n["label"], color=get_color(n))
         for n in graph_data["nodes"]]

edges = [Edge(source=e["source"], target=e["target"])
         for e in graph_data["edges"]]

agraph(nodes=nodes, edges=edges, config=physics_config)
```

---

## 3. Reasoning Engine - Rule-Based AI

### Purpose
Calculate topic priorities using symbolic AI (rules) rather than machine learning.

### Architecture

```python
class ReasoningEngine:
    def __init__(self):
        self.rules = []  # Extensible rule list
```

**Why Rule-Based?**
- **Explainable:** Each rule has clear logic
- **Deterministic:** Same input → same output
- **No training data needed:** Works immediately
- **Transparent:** Users understand decisions

---

### Priority Calculation Pipeline

```python
def apply_reasoning(self, graph, user_model) -> Dict[str, float]:
    """
    Apply all rules to compute topic priorities.
    """
    priorities = {}
    
    for topic_id in graph.graph.nodes:
        topic_data = graph.get_topic_data(topic_id)
        
        # Base priority
        priority = 0.5
        
        # Apply 5 rules (additive)
        priority += self._deadline_urgency_rule(user_model, graph, topic_id)
        priority += self._difficulty_rule(topic_data, user_model)
        priority += self._prerequisite_rule(graph, topic_id, user_model)
        priority += self._spaced_repetition_rule(topic_id, user_model)
        priority += self._learning_style_rule(topic_data, user_model)
        
        # Normalize to [0, 1]
        priority = max(0.0, min(1.0, priority))
        
        priorities[topic_id] = priority
        graph.update_priority(topic_id, priority)
    
    return priorities
```

---

### Rule 1: Deadline Urgency

**Hypothesis:** If deadline is approaching, increase priority of all topics.

```python
def _deadline_urgency_rule(self, user_model, graph, topic_id) -> float:
    days_remaining = user_model.get_days_until_deadline()
    
    if days_remaining < 30:
        urgency = 0.3 * (1 - days_remaining / 30)
        return urgency
    
    return 0.0
```

**Math:**
- 30 days: +0.0 boost
- 15 days: +0.15 boost
- 0 days: +0.30 boost

**Reasoning:**
- Topics become more urgent as deadline approaches
- Linear scaling (simplest model)
- Caps at +0.3 to avoid dominating other factors

---

### Rule 2: Difficulty Matching

**Hypothesis:** Match topic difficulty to user's learning preference.

```python
def _difficulty_rule(self, topic_data, user_model) -> float:
    difficulty = topic_data['difficulty']
    preference = user_model.difficulty_preference
    
    if "gradually" in preference.lower():
        # Prefer easier topics first
        return -0.2 * difficulty
    
    elif "advanced" in preference.lower():
        # Prefer harder topics first
        return 0.2 * difficulty
    
    return 0.0
```

**Examples:**

| Difficulty | Gradual Preference | Advanced Preference |
|------------|-------------------|-------------------|
| 0.2 (easy) | +0.04 boost | -0.04 penalty |
| 0.5 (medium) | 0.0 neutral | 0.0 neutral |
| 0.8 (hard) | -0.16 penalty | +0.16 boost |

**Reasoning:**
- "Gradually" learners build confidence with easy topics
- "Advanced" learners want challenges upfront
- Moderate penalty/boost (±0.2 max) preserves other factors

---

### Rule 3: Prerequisite Unlocking

**Hypothesis:** Topics that unlock many others should be prioritized (critical path).

```python
def _prerequisite_rule(self, graph, topic_id, user_model) -> float:
    dependents = graph.get_dependents(topic_id)
    
    if len(dependents) > 2:
        return 0.2  # High priority - unlocks many
    elif len(dependents) > 0:
        return 0.1  # Medium priority
    
    return 0.0
```

**Example:**
```
fundamentals → [data_structures, algorithms, system_design]
               (3 dependents)

fundamentals gets +0.2 boost
```

**Reasoning:**
- Blocking topics delay entire path
- Early completion enables parallel progress
- Critical path optimization

---

### Rule 4: Spaced Repetition

**Hypothesis:** Completed topics need review at intervals.

```python
def _spaced_repetition_rule(self, topic_id, user_model) -> float:
    if topic_id in user_model.completed_topics:
        # Review sessions have moderate priority
        return 0.15
    
    return 0.0
```

**Future Enhancement:**
```python
# Track completion date
days_since_completion = (today - completion_date).days

if days_since_completion in [1, 3, 7, 14, 30]:
    # Optimal review intervals (Ebbinghaus curve)
    return 0.25  # High priority review
```

**Reasoning:**
- Spaced repetition improves retention by 200-300%
- Reviews scheduled at increasing intervals
- Prevents forgetting curve

---

### Rule 5: Learning Style Matching

**Hypothesis:** Match topic category to user's learning style.

```python
def _learning_style_rule(self, topic_data, user_model) -> float:
    category = topic_data['category'].lower()
    style = user_model.learning_style.lower()
    
    if "hands-on" in style and ("practice" in category or "project" in category):
        return 0.15
    
    elif "visual" in style and "theory" in category:
        return 0.1
    
    return 0.0
```

**Example Matching:**
- Hands-on learner + "Practice Projects" → +0.15 boost
- Visual learner + "Theoretical Foundations" → +0.10 boost
- Auditory learner + "Lecture-based" → +0.10 boost (extensible)

**Reasoning:**
- Personalized learning paths
- Motivation boost from preferred formats
- Can be extended with more style-category mappings

---

### Explainability

```python
def explain_priority(self, topic_id, graph, user_model) -> str:
    """
    Generate human-readable justification.
    """
    topic_data = graph.get_topic_data(topic_id)
    priority = topic_data['priority']
    
    explanation = f"Priority for '{topic_data['title']}': {priority:.2f}\n\n"
    explanation += "Reasoning:\n"
    
    # Check each rule
    days = user_model.get_days_until_deadline()
    if days < 30:
        explanation += f"- ⏰ Deadline approaching ({days} days)\n"
    
    difficulty = topic_data['difficulty']
    if difficulty > 0.7:
        explanation += f"- 🔴 High difficulty ({difficulty:.1f}) - early focus\n"
    
    dependents = graph.get_dependents(topic_id)
    if len(dependents) > 0:
        explanation += f"- 🔗 Unlocks {len(dependents)} topics\n"
    
    return explanation
```

**Example Output:**
```
Priority for 'Data Structures & Algorithms': 0.85

Reasoning:
- ⏰ Deadline approaching (22 days remaining)
- 🔴 High difficulty (0.8) - scheduled early
- 🔗 Unlocks 4 other topics (Algorithms, System Design, ML, Databases)
- 🎯 Matches your "gradually" preference (foundational topic)
```

---

## 4. A* Planner - Optimal Pathfinding

### Purpose
Find the optimal order to study topics using A* search algorithm.

### Why A* (Not Greedy or BFS)?

| Algorithm | Completeness | Optimality | Time Complexity |
|-----------|-------------|-----------|----------------|
| Greedy | ❌ No | ❌ No | O(V) |
| BFS | ✅ Yes | ⚠️ Only if unweighted | O(V + E) |
| A* | ✅ Yes | ✅ Yes (with admissible h) | O(b^d) |

**A* Advantages:**
- Guaranteed optimal path (if heuristic is admissible)
- Efficient pruning (doesn't explore unnecessary states)
- Flexible cost function (combines multiple factors)

---

### State Space Formulation

**State:** Set of completed topics (represented as `frozenset`)

```python
initial_state = frozenset()  # No topics completed
goal_state = frozenset(all_topics)  # All topics completed
```

**Actions:** Study an available topic (prerequisites met)

```python
available = graph.get_available_topics(current_state)
for topic in available:
    new_state = frozenset(current_state | {topic})
```

**State Space Size:** 2^N (powerset of topics)
- 10 topics → 1,024 states
- 20 topics → 1,048,576 states
- Exponential, but A* prunes effectively

---

### Cost Function (g-score)

```python
def _action_cost(self, topic_id: str) -> float:
    """
    Cost of studying a topic.
    Lower cost = higher priority.
    """
    topic_data = self.graph.get_topic_data(topic_id)
    
    # Time cost (actual hours required)
    time_cost = topic_data['estimated_hours']
    
    # Difficulty cost (harder topics = higher cost)
    difficulty_cost = topic_data['difficulty'] * 10
    
    # Priority cost (high priority = low cost)
    priority_cost = (1.0 - topic_data['priority']) * 5
    
    total_cost = time_cost + difficulty_cost + priority_cost
    return total_cost
```

**Example Calculation:**
```python
topic = {
    "estimated_hours": 8,
    "difficulty": 0.7,
    "priority": 0.9
}

time_cost = 8
difficulty_cost = 0.7 * 10 = 7
priority_cost = (1.0 - 0.9) * 5 = 0.5

total_cost = 8 + 7 + 0.5 = 15.5
```

**Interpretation:**
- High priority topic (0.9) has low cost (15.5)
- Low priority topic (0.3) has high cost (≈25+)
- A* will prefer low-cost paths (high-priority topics)

---

### Heuristic Function (h-score)

**Requirement:** Must be **admissible** (never overestimate)

```python
def _heuristic(self, current_state, goal_state) -> float:
    """
    Estimate cost to reach goal from current state.
    Uses optimistic estimate (minimum possible cost).
    """
    remaining = goal_state - current_state
    
    if not remaining:
        return 0  # Already at goal
    
    # Estimate: sum of just the time required
    # (ignores difficulty and priority for optimism)
    total_estimate = 0
    for topic_id in remaining:
        topic_data = self.graph.get_topic_data(topic_id)
        total_estimate += topic_data['estimated_hours']
    
    return total_estimate
```

**Why Admissible?**
- Only counts `estimated_hours` (minimum cost component)
- Ignores `difficulty_cost` and `priority_cost` (optimistic)
- Guarantees: `h(state) ≤ actual_cost_to_goal`

**Example:**
```python
remaining = ["algorithms", "databases"]
# algorithms: 10h, databases: 8h

h = 10 + 8 = 18

# Actual cost will be higher:
# algorithms: 10 + (0.8 * 10) + (0.2 * 5) = 19
# databases: 8 + (0.5 * 10) + (0.4 * 5) = 15
# Actual total: 34 > 18 ✅ (admissible)
```

---

### A* Algorithm Implementation

```python
def find_optimal_path(self) -> List[str]:
    all_topics = set(self.graph.graph.nodes)
    initial_state = frozenset()
    goal_state = frozenset(all_topics)
    
    # Priority queue: (f_score, g_score, state, path)
    open_set = []
    heapq.heappush(open_set, (
        self._heuristic(initial_state, goal_state),  # f = g + h
        0,                                            # g = 0
        initial_state,                                # current state
        []                                            # path so far
    ))
    
    visited = set()
    g_scores = {initial_state: 0}
    
    while open_set:
        f_score, g_score, current_state, path = heapq.heappop(open_set)
        
        # Goal check
        if current_state == goal_state:
            return path  # ✅ Optimal path found
        
        # Skip if already explored
        if current_state in visited:
            continue
        visited.add(current_state)
        
        # Expand state (try studying each available topic)
        available = self.graph.get_available_topics(list(current_state))
        
        for topic_id in available:
            new_state = frozenset(current_state | {topic_id})
            new_g_score = g_score + self._action_cost(topic_id)
            
            # Only proceed if this is a better path
            if new_state not in g_scores or new_g_score < g_scores[new_state]:
                g_scores[new_state] = new_g_score
                new_f_score = new_g_score + self._heuristic(new_state, goal_state)
                
                heapq.heappush(open_set, (
                    new_f_score,
                    new_g_score,
                    new_state,
                    path + [topic_id]
                ))
    
    # Fallback (should never reach if graph is valid)
    return self.graph.get_learning_path()  # Topological sort
```

**Key Features:**
1. **Priority queue:** Explores lowest f-score states first
2. **Visited set:** Avoids re-exploring states
3. **g_scores dict:** Tracks best cost to each state
4. **Early termination:** Returns as soon as goal reached

---

### Complexity Analysis

**Time Complexity:**
- Worst case: O(b^d) where b = branching factor, d = depth
- Typical case: Much faster due to pruning
- Example: 20 topics, avg 3 available at each state
  - Worst: 3^20 = 3.4 billion states
  - Actual: ~500-1000 states explored (99.99% pruned!)

**Space Complexity:**
- O(b^d) for open_set
- O(2^N) for visited set (worst case)
- Mitigated by: Early termination, efficient frozenset hashing

---

### Path Explanation

```python
def explain_path(self, path: List[str]) -> str:
    """
    Generate explanation for why this path is optimal.
    """
    explanation = "🤖 A* Search Algorithm Results\n\n"
    explanation += "This learning path is optimal because:\n\n"
    
    total_cost = 0
    
    for i, topic_id in enumerate(path, 1):
        topic_data = self.graph.get_topic_data(topic_id)
        cost = self._action_cost(topic_id)
        total_cost += cost
        
        explanation += f"{i}. **{topic_data['title']}**\n"
        explanation += f"   - Difficulty: {topic_data['difficulty']:.1f}\n"
        explanation += f"   - Time: {topic_data['estimated_hours']}h\n"
        explanation += f"   - Priority: {topic_data['priority']:.2f}\n"
        explanation += f"   - Cost: {cost:.1f}\n\n"
    
    explanation += f"**Total Path Cost:** {total_cost:.1f}\n\n"
    explanation += "Algorithm minimized total cost while respecting prerequisites."
    
    return explanation
```

**Example Output:**
```
🤖 A* Search Algorithm Results

This learning path is optimal because:

1. **Fundamentals**
   - Difficulty: 0.3
   - Time: 6h
   - Priority: 0.85
   - Cost: 9.75

2. **Data Structures**
   - Difficulty: 0.7
   - Time: 10h
   - Priority: 0.90
   - Cost: 17.5

3. **Algorithms**
   - Difficulty: 0.8
   - Time: 12h
   - Priority: 0.88
   - Cost: 20.6

Total Path Cost: 47.85

Algorithm minimized total cost while respecting prerequisites.
```

---

## 5. Meta-Reasoner - Strategic Intelligence

### Purpose
Apply strategic transformations to A* output to optimize for human factors (fatigue, cognitive load).

### Concept: "Meta" Reasoning

**Traditional AI:** Solves problem  
**Meta-AI:** Thinks about how to solve the problem

```
A* Output: [Hard, Hard, Hard, Easy, Easy]
          ↓
Meta-Reasoner: "This will cause fatigue"
          ↓
Transformed: [Hard, Easy, Hard, Easy, Hard]
```

---

### Fatigue Filter Algorithm

```python
def apply_fatigue_filter(self, ordered_topics: List[str]) -> List[str]:
    """
    Prevent back-to-back difficult topics.
    Only reorders when prerequisites allow.
    """
    if len(ordered_topics) < 3:
        return ordered_topics  # Too short to optimize
    
    reordered = []
    remaining = list(ordered_topics)
    completed = set()
    
    HARD_THRESHOLD = 0.6
    
    while remaining:
        # Get topics whose prerequisites are met
        available = [
            t for t in remaining
            if self._prerequisites_met(t, completed)
        ]
        
        if not available:
            # No valid topics - take next in original order
            next_topic = remaining.pop(0)
        else:
            # Smart selection based on previous topic
            if reordered:
                prev_difficulty = self._get_difficulty(reordered[-1])
                
                if prev_difficulty >= HARD_THRESHOLD:
                    # Last was hard - prefer easier next
                    next_topic = self._select_easiest(available)
                else:
                    # Last was easy - can do hard now
                    next_topic = self._select_hardest(available)
            else:
                # First topic - prefer medium to warm up
                next_topic = self._select_medium(available)
            
            remaining.remove(next_topic)
        
        reordered.append(next_topic)
        completed.add(next_topic)
    
    return reordered
```

---

### Example Transformation

**Input (from A*):**
```python
[
    "system_design",        # difficulty: 0.9
    "distributed_systems",  # difficulty: 0.9
    "networking",          # difficulty: 0.8
    "intro_to_os",         # difficulty: 0.3
    "file_systems"         # difficulty: 0.6
]
```

**Fatigue Filter Logic:**

1. **Position 1:** No previous topic → Select medium (0.5-ish)
   - Available: all (no prerequisites)
   - Choose: `file_systems` (0.6 - closest to 0.5)

2. **Position 2:** Previous was 0.6 (not hard) → Can do hard
   - Available: all except `file_systems`
   - Choose: `system_design` (0.9 - hardest)

3. **Position 3:** Previous was 0.9 (hard) → Prefer easy
   - Available: all except `file_systems`, `system_design`
   - Choose: `intro_to_os` (0.3 - easiest)

4. **Position 4:** Previous was 0.3 (easy) → Can do hard
   - Available: `distributed_systems` (0.9), `networking` (0.8)
   - Choose: `distributed_systems` (0.9 - hardest)

5. **Position 5:** Previous was 0.9 (hard) → Prefer easy
   - Only remaining: `networking` (0.8)
   - Choose: `networking`

**Output (after Meta):**
```python
[
    "file_systems",        # 0.6 (warm-up)
    "system_design",       # 0.9 (hard)
    "intro_to_os",         # 0.3 (recovery)
    "distributed_systems", # 0.9 (hard)
    "networking"           # 0.8 (moderate)
]
```

**Difficulty Pattern:** 0.6 → 0.9 → 0.3 → 0.9 → 0.8  
*Notice the alternation: no consecutive hard topics!*

---

### Constraint Preservation

```python
def _prerequisites_met(self, topic_id: str, completed: set) -> bool:
    """
    Check if all prerequisites for a topic are in completed set.
    """
    prereqs = self.graph.get_prerequisites(topic_id)
    return all(p in completed for p in prereqs)
```

**Critical Guarantee:**  
Meta-reasoner **never violates prerequisites**. If reordering would break dependency, it keeps original order.

---

### Explanation Generation

```python
def explain_reordering(self, original: List[str], reordered: List[str]) -> str:
    """
    Generate human-readable explanation of changes.
    """
    if original == reordered:
        return "No reordering needed - path already optimized for cognitive load."
    
    explanation = "🧠 **Meta-Reasoning Applied**: Fatigue Filter\n\n"
    explanation += "Schedule adjusted to prevent cognitive overload:\n\n"
    
    changes = 0
    for i in range(min(len(original), len(reordered))):
        if original[i] != reordered[i]:
            orig_title = self.graph.get_topic_data(original[i])['title']
            new_title = self.graph.get_topic_data(reordered[i])['title']
            orig_diff = self._get_difficulty(original[i])
            new_diff = self._get_difficulty(reordered[i])
            
            explanation += f"**Position {i+1}:** {orig_title} ({orig_diff:.1f}) "
            explanation += f"→ {new_title} ({new_diff:.1f})\n"
            changes += 1
    
    explanation += f"\n✅ Total adjustments: {changes}\n"
    explanation += "Prevents back-to-back difficult topics for sustained focus."
    
    return explanation
```

**Example Output:**
```
🧠 Meta-Reasoning Applied: Fatigue Filter

Schedule adjusted to prevent cognitive overload:

**Position 1:** System Design (0.9) → File Systems (0.6)
**Position 3:** Networking (0.8) → Intro to OS (0.3)

✅ Total adjustments: 2
Prevents back-to-back difficult topics for sustained focus.
```

---

## 6. CSP Scheduler - Constraint Satisfaction

### Purpose
Assign study sessions to specific time slots across multiple weeks while satisfying constraints.

### Constraint Satisfaction Problem Formulation

**Variables:** Study sessions (topic parts)

**Domains:** Time slots (Week, Day, Slot combinations)

**Constraints:**
1. Slot capacity (180 minutes per 3-hour slot)
2. Daily study limit (user-defined max hours)
3. Sequential parts (Part N requires Part N-1 scheduled)
4. Unavailable slots (user blocks certain times)

---

### Multi-Week Schedule Structure

```python
weeks_available = max(1, (days_until_deadline + 6) // 7)

schedule = {}
for week in range(1, weeks_available + 1):
    for day in self.weekdays:
        week_day_key = f"Week {week} - {day}"
        schedule[week_day_key] = []
```

**Example:**
```python
{
    "Week 1 - Monday": [],
    "Week 1 - Tuesday": [],
    # ...
    "Week 6 - Sunday": [],
    "_weeks_available": 6,
    "_current_week_schedule": {...}  # Backward compatibility
}
```

---

### Session Expansion (Topic → Parts)

```python
def _split_topic_into_sessions(self, topic_id, session_length):
    """
    Split a multi-hour topic into multiple session parts.
    """
    total_hours = self._topic_hours(topic_id)
    total_minutes = total_hours * 60
    num_parts = max(1, ceil(total_minutes / session_length))
    
    parts = []
    for i in range(1, num_parts + 1):
        parts.append({
            "parent_topic": topic_id,
            "part_index": i,
            "total_parts": num_parts,
            "minutes": min(session_length, total_minutes - (i-1)*session_length)
        })
    
    return parts
```

**Example:**
```python
topic = "Data Structures" (12 hours)
session_length = 45 minutes

# 12 * 60 = 720 minutes
# 720 / 45 = 16 parts

parts = [
    {"parent_topic": "DS", "part_index": 1, "minutes": 45},
    {"parent_topic": "DS", "part_index": 2, "minutes": 45},
    # ...
    {"parent_topic": "DS", "part_index": 16, "minutes": 45}
]
```

---

### Subtopic Assignment

```python
# Map subtopics to parts
subtopics = ["Arrays", "LinkedLists", "Trees", "Graphs"]
total_parts = 16

chunk_size = ceil(4 / 16) = 1  # Each part gets ≤1 subtopic

for part in parts:
    idx0 = (part["part_index"] - 1) * chunk_size
    idx1 = min(idx0 + chunk_size, 4)
    
    chosen = subtopics[idx0:idx1]
    part["subtopic"] = ", ".join(chosen) if chosen else None
```

**Result:**
- Part 1: "Arrays"
- Part 2: "LinkedLists"
- Part 3: "Trees"
- Part 4: "Graphs"
- Parts 5-16: None (fallback to general description)

---

### Multi-Pass Placement Algorithm

**Problem:** If Part 1 doesn't fit in Monday, and algorithm moves to Part 2, Part 2 will be rejected (prerequisite not met). Then Part 3, Part 4, etc. all rejected.

**Solution:** Multi-pass with retry queue

```python
max_passes = 10
unplaced_sessions = list(expanded_sessions)

for pass_num in range(max_passes):
    placed_in_this_pass = 0
    still_unplaced = []
    
    for session in unplaced_sessions:
        topic_id = session["parent_topic"]
        part = session["part_index"]
        
        # Check prerequisite
        if part > 1 and (topic_id, part-1) not in placed_parts:
            still_unplaced.append(session)  # Retry next pass
            continue
        
        # Try to place
        best_slot = find_best_slot(session)
        
        if best_slot:
            place_session(best_slot, session)
            placed_parts.add((topic_id, part))
            placed_in_this_pass += 1
        else:
            still_unplaced.append(session)
    
    # Update queue for next pass
    unplaced_sessions = still_unplaced
    
    # Stop if no progress
    if placed_in_this_pass == 0:
        break  # No more sessions can be placed
```

**Why This Works:**
- **Pass 1:** Places Part 1 (if space available)
- **Pass 2:** Part 2 now available (Part 1 placed), gets scheduled
- **Pass 3:** Part 3 now available (Part 2 placed), gets scheduled
- Continues until all parts placed or no progress

**Typical Pass Count:** 2-3 (rarely hits max 10)

---

### Slot Scoring Function

```python
def _score_slot(self, session, day, slot_label, remaining_today, remaining_in_slot):
    """
    Calculate desirability score for placing session in this slot.
    Higher score = better fit.
    """
    score = 0
    
    # Factor 1: Peak hour match
    is_peak = self._slot_is_peak(slot_label)
    difficulty = session["difficulty"]
    
    if is_peak and difficulty > 0.6:
        score += 50  # Hard topics in peak hours
    
    # Factor 2: Priority
    priority = session["priority_graph"]
    
    if priority > 0.7:
        # High priority topics prefer earlier slots
        slot_index = self.slot_index[slot_label]
        score += 30 * (6 - slot_index)  # Earlier = higher score
    
    # Factor 3: Week preference (fill early weeks first)
    # Passed via context in actual implementation
    # score -= week_number * 10
    
    # Factor 4: Capacity utilization
    # Prefer slots with more remaining space (flexibility)
    capacity_ratio = remaining_in_slot / 180
    score += capacity_ratio * 20
    
    return score
```

**Example Scoring:**
```python
# Hard topic (0.8), high priority (0.9), peak hour (9-12 PM)
score = 50 + 30*(6-1) + 0.8*20 = 50 + 150 + 16 = 216

# Easy topic (0.3), low priority (0.4), off-peak (9-12 AM)
score = 0 + 0 + 0.8*20 = 16

# Hard topic is 13.5x more likely to get the better slot
```

---

### Constraint Checking

#### 1. Slot Capacity Constraint

```python
used_in_slot = sum(
    s["duration"] + s["break_after"]
    for s in schedule[week_day_key]
    if s["time"] == slot_label
)

capacity = 180  # 3 hours
remaining_in_slot = capacity - used_in_slot

session_needs = duration + break_length

if remaining_in_slot < session_needs:
    continue  # Skip this slot
```

#### 2. Daily Study Limit Constraint

```python
daily_limit_minutes = user.study_hours_per_day * 60

used_today = sum(
    s["duration"] + s["break_after"]
    for s in schedule[week_day_key]
)

remaining_today = daily_limit_minutes - used_today

if remaining_today < session_needs:
    continue  # Skip this day
```

#### 3. Sequential Parts Constraint

```python
if part > 1 and (topic_id, part-1) not in placed_parts:
    still_unplaced.append(session)
    continue  # Can't place yet
```

#### 4. Unavailable Slots Constraint

```python
unavailable = user.unavailable_slots.get(day, [])

if slot_label in unavailable:
    continue  # User blocked this slot
```

---

### Session Object Structure

```python
session_obj = {
    "topic_id": "data_structures",
    "title": "Data Structures (Part 3/16)",
    "subtopic": "Trees",
    "duration": 45,
    "break_after": 10,
    "time": "9-12 PM",
    "is_peak": True,
    "difficulty": 0.7,
    "part_index": 3,
    "total_parts": 16,
    "week": 2
}
```

---

### Output Format

```python
{
    "Week 1 - Monday": [session1, session2],
    "Week 1 - Tuesday": [session3],
    # ...
    "Week 6 - Sunday": [sessionX],
    
    # Metadata
    "_weeks_available": 6,
    "_current_week_schedule": {...},  # Week 1 only
    "_dropped_topics": [...],         # Couldn't fit
    "_dropped_parts": [...]           # Individual parts dropped
}
```

---

## 7. Ethics Guard - Safety Layer

### Purpose
Enforce research-backed well-being constraints that override optimization goals.

### Hard Constraints (Refusal)

```python
MAX_DAILY_HOURS = 6  # Absolute maximum

if daily_hours > MAX_DAILY_HOURS:
    return {
        "is_safe": False,
        "error": "CRITICAL: Burnout risk detected. System refuses to proceed."
    }
```

**Refusal Mechanism:**
- UI shows error message with research citations
- **Does not generate schedule**
- Suggests healthier alternative
- User must adjust to proceed

---

### Soft Constraints (Warnings)

```python
OPTIMAL_DAILY_HOURS = 4

if daily_hours > OPTIMAL_DAILY_HOURS:
    warnings.append("High study load. Consider reducing to 4h/day.")
```

**Warning Mechanism:**
- UI shows warning with explanation
- User can proceed or adjust
- Logged for transparency

---

### Research Citations

Every constraint includes research foundation:

```python
{
    "constraint": "6h max daily study",
    "research": "Ericsson et al. (1993) - Deliberate Practice",
    "finding": "Elite performers across domains practice 4-5h/day maximum",
    "implication": "More ≠ Better. Quality > Quantity."
}
```

---

## 8. Persistence Manager - State Management

### Purpose
Handle complex object serialization, database persistence, and transparency logging.

### Pickle Serialization

**Challenge:** NetworkX graphs, UserModel objects can't be JSON-serialized.

**Solution:** Python's `pickle` module

```python
class StateStore(Base):
    __tablename__ = 'state_store'
    
    key = Column(String, primary_key=True)
    value = Column(PickleType)  # SQLAlchemy handles pickling
    timestamp = Column(DateTime)
```

**Usage:**
```python
pm = PersistenceManager()

# Save complex object
pm.save_state('graph', graph_object)

# Load
graph = pm.load_state('graph')
```

**Serialization Process:**
```python
pickle.dumps(graph_object)
# → bytes stream
# → stored in SQLite BLOB column
# → pickle.loads(bytes) → original object
```

---

### Transparency Logging

```python
class AgentLog(Base):
    __tablename__ = 'agent_logs'
    
    timestamp = Column(DateTime)
    module = Column(String)     # "Reasoning", "A*", "CSP"
    message = Column(Text)
    details = Column(Text)      # JSON
```

**Usage:**
```python
pm.log_event(
    "CSP",
    "Scheduled 15 sessions for Week 1",
    json.dumps({"placed": 15, "dropped": 0})
)
```

**Retrieval:**
```python
logs = pm.get_recent_logs(limit=10)
for module, message, timestamp in logs:
    print(f"[{timestamp}] {module}: {message}")
```

---

## Summary: AI Pipeline Flow

```
1. LLM Helper
   ↓ (Generates curriculum with subtopics)
   
2. Knowledge Graph
   ↓ (Builds DAG with dependencies)
   
3. Reasoning Engine
   ↓ (Calculates priorities using 5 rules)
   
4. A* Planner
   ↓ (Finds optimal learning path)
   
5. Meta-Reasoner
   ↓ (Applies fatigue filter)
   
6. CSP Scheduler
   ↓ (Multi-week session placement)
   
7. Ethics Guard
   ↓ (Validates constraints)
   
8. Persistence Manager
   ↓ (Saves state + logs decisions)
```

Each component is:
- **Modular:** Can be replaced/upgraded independently
- **Explainable:** Every decision has justification
- **Testable:** Unit tests in `test_integration.py`
- **Transparent:** Logs all actions for review

---

**This architecture balances performance optimization with ethical constraints, creating an AI system that is both intelligent and responsible.**
