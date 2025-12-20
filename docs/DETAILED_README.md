# 🧠 Adaptive AI Study Planner

An intelligent, ethically-designed study planning system that combines multiple AI techniques to create personalized learning roadmaps and schedules.

## 🌟 Overview

The Adaptive AI Study Planner is not just another task scheduler—it's a **multi-agent AI system** that applies cutting-edge techniques from search algorithms, constraint satisfaction, rule-based reasoning, and cognitive science to optimize your learning journey while prioritizing your well-being.

### Key Features

- 🤖 **AI-Powered Curriculum Generation** - LLM-based topic breakdown with subtopics
- 🧮 **A* Search Algorithm** - Finds optimal learning path considering prerequisites
- 🧠 **Rule-Based Reasoning Engine** - Adapts priorities based on deadlines, difficulty, and preferences
- 🔄 **Meta-Reasoning Layer** - Prevents cognitive overload through strategic reordering
- ⚖️ **Ethics Guard** - Refuses schedules that risk burnout (research-backed constraints)
- 📊 **CSP Scheduler** - Multi-week constraint satisfaction with sequential part placement
- 💾 **Persistence Layer** - Session continuity with complex object serialization
- 📝 **Transparency Logging** - Track every AI decision for explainability
- 📈 **Interactive Visualizations** - Physics-based knowledge graph, multi-week schedule tabs

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd "Adaptive Ai study planner"

# Install dependencies
pip install -r requirements.txt

# (Optional) Set up Gemini API key for LLM features
# Create .env file:
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

### Running the App

```bash
streamlit run pages/1_🎯_Set_Goal.py
```

### First-Time Setup

1. **Set Your Goal** - Select subjects or enter custom topics
2. **Configure Timeline** - Set deadline and daily study hours
3. **Choose Preferences** - Session length, break time, peak hours
4. **Select Availability** - Mark unavailable days and time slots
5. **Generate Roadmap** - Watch AI work through 6 intelligent steps
6. **Rate Confidence** - Indicate weakness areas for priority boost
7. **Generate Schedule** - CSP creates multi-week study plan
8. **View Progress** - Track completion and analytics

## 📁 Project Structure

```
Adaptive Ai study planner/
├── pages/                          # Streamlit multi-page app
│   ├── 1_🎯_Set_Goal.py           # Goal setting with ethics checks
│   ├── 2_📊_View_Roadmap.py       # Interactive dependency graph
│   ├── 3_📅_View_Schedule.py      # Multi-week schedule display
│   ├── 4_📈_Progress.py           # Analytics and tracking
│   └── 5_⚙️_Settings.py           # API configuration
│
├── backend/                        # AI components and logic
│   ├── llm_helper.py              # Gemini LLM integration
│   ├── state_graph.py             # Knowledge graph (NetworkX)
│   ├── reasoner.py                # Rule-based reasoning engine
│   ├── a_star_planner.py          # A* search algorithm
│   ├── meta_reasoner.py           # Strategic path optimization
│   ├── scheduler.py               # CSP-based multi-week scheduler
│   ├── user_model.py              # User preference modeling
│   ├── ethics.py                  # Ethical constraint enforcement
│   └── db.py                      # SQLAlchemy persistence + logging
│
├── test_integration.py             # Comprehensive test suite
├── reset_db.py                     # Database reset utility
└── requirements.txt                # Python dependencies
```

## 🧪 Testing

Run comprehensive integration tests:

```bash
python test_integration.py
```

Tests cover:
- Graph management and dependencies
- User model configurations
- Reasoning engine priority calculation
- A* pathfinding
- Meta-reasoning fatigue filter
- CSP scheduler with multi-week support
- Ethics guard burnout detection
- Persistence and logging

## 🎯 AI Components

### 1. **LLM Helper** (`llm_helper.py`)
- Uses Google Gemini API for curriculum generation
- Generates structured topics with subtopics, prerequisites, difficulty
- Fallback templates when API unavailable
- Explainability through natural language justifications

### 2. **Knowledge Graph** (`state_graph.py`)
- NetworkX directed graph for topic relationships
- Active representation - recalculates priorities dynamically
- Topological sorting for dependency resolution
- Supports visualization with physics-based layout

### 3. **Reasoning Engine** (`reasoner.py`)
- 5 intelligent rules:
  - Deadline urgency (< 30 days boost)
  - Difficulty matching (gradual vs. advanced)
  - Prerequisite unlocking (topics that enable others)
  - Spaced repetition (review scheduling)
  - Learning style matching (hands-on, visual, etc.)
- Explainable priorities for transparency

### 4. **A* Planner** (`a_star_planner.py`)
- Cost function: `time + difficulty + (1 - priority)`
- Heuristic: optimistic estimate of remaining work
- Guarantees optimal path if prerequisites form DAG
- Explains path cost breakdown

### 5. **Meta-Reasoner** (`meta_reasoner.py`)
- "Thinking about thinking" layer
- Fatigue filter: prevents Hard → Hard → Hard sequences
- Reorders to Hard → Easy → Hard when possible
- Preserves prerequisite constraints

### 6. **CSP Scheduler** (`scheduler.py`)
- Multi-week scheduling (calculates weeks until deadline)
- Multi-pass algorithm for sequential part placement
- Slot capacity management (3-hour slots)
- Daily study hour limits with overflow protection
- Peak hour prioritization for difficult topics
- Subtopic assignment per session part

### 7. **Ethics Guard** (`ethics.py`)
- Research-backed constraints:
  - Max 6h/day sustainable study
  - 15-20% break ratio (cognitive load theory)
  - No studying past 11 PM (sleep protection)
  - Mandatory rest day per week
- **REFUSES** to create burnout-risk schedules
- Suggests healthier alternatives

### 8. **Persistence Layer** (`db.py`)
- SQLAlchemy + SQLite + Pickle
- Stores complex objects (Graph, UserModel)
- Session continuity across restarts
- Transparency logs for AI decisions
- Automatic cleanup of old logs

## 🔬 Technical Highlights

### Multi-Week Scheduler Algorithm

**Problem:** Original scheduler only generated 1 week, leaving topics unscheduled.

**Solution:** 
```python
weeks_available = max(1, (days_until_deadline + 6) // 7)
schedule = {f"Week {week} - {day}": [] for week in range(1, weeks_available+1)}
```

**Innovation:** Multi-pass placement ensures Part 1 before Part 2:
```python
for pass_num in range(max_passes):
    for session in unplaced_sessions:
        if part > 1 and (topic_id, part-1) not in placed_parts:
            still_unplaced.append(session)  # Retry next pass
            continue
        # ... placement logic ...
```

### Intelligent Loading State

**UX Innovation:** Show AI thinking in real-time using `st.status()`:
```python
with st.status("🤖 AI Agent Working...", expanded=True) as status:
    st.write("🧠 Consulting LLM...")
    st.write("🕸️ Constructing Knowledge Graph...")
    st.write("⚡ Running A* Search...")
    status.update(label="✅ Complete!", state="complete")
```

### Gamified Progress Sidebar

**Every page shows:**
- Progress bar (0-100%)
- Current step indicator
- Next action prompt
- Motivational messaging

## 📊 Data Flow

```
User Input (Goal + Preferences)
    ↓
LLM Helper → Generate Curriculum with Subtopics
    ↓
Knowledge Graph → Build dependency network
    ↓
Reasoning Engine → Calculate topic priorities
    ↓
A* Planner → Find optimal learning path
    ↓
Meta-Reasoner → Apply fatigue filter
    ↓
CSP Scheduler → Multi-week session placement
    ↓
Streamlit UI → Interactive visualization
    ↓
Persistence Layer → Save state + log decisions
```

## 🎨 UI/UX Features

### Interactive Knowledge Graph
- Physics-based layout (Barnes-Hut algorithm)
- Color coding: Green (completed), Blue (available), Red (locked)
- Hover tooltips with topic details
- Smooth edges and optimal spacing

### Multi-Week Schedule Display
- Tabbed interface for each week
- Expandable day sections
- Subtopic-based session titles (not part numbers)
- Visual dataframe with column config
- Full-width, 600px height for readability

### Progress Tracking
- Completion percentage
- Time invested vs. remaining
- Topic difficulty distribution
- Upcoming deadlines

## ⚖️ Ethics & Safety

### Why Ethics Matter

Traditional AI optimizes for **performance**. This system optimizes for **sustainable success**.

**Research Foundation:**
- Burnout Prevention (Maslach & Leiter, 2016)
- Spaced Learning (Ebbinghaus, 1885)
- Cognitive Load Theory (Sweller, 1988)
- Sleep-Learning Connection (Walker, 2017)

### Constraints Enforced

```python
MAX_DAILY_HOURS = 6       # Refuses schedules > 6h/day
OPTIMAL_DAILY_HOURS = 4   # Recommends 4h/day
MIN_BREAK_RATIO = 0.15    # 15% minimum breaks
LATE_NIGHT_CUTOFF = 23    # No studying past 11 PM
```

**Example:** User sets 8h/day → System refuses and explains why

## 🔍 Explainability

Every AI decision is logged and explainable:

```python
pm.log_event("Reasoning", "Calculated 26 topic priorities", 
             "Deadline: 45 days, Style: hands-on")

pm.log_event("A*", "Generated optimal path with 26 topics",
             "First: os_fundamentals, Total cost: 142.5")

pm.log_event("Meta", "Applied fatigue filter",
             "Reordered 3 topics to prevent cognitive overload")
```

**Transparency Page** (Settings) shows:
- Recent AI decisions
- Module responsible (Reasoning/CSP/A*/Meta)
- Timestamp and details
- Justification for each choice

## 🐛 Troubleshooting

### Issue: No topics scheduled
**Cause:** Insufficient time slots  
**Solution:** Add more study slots or extend deadline  
**Detection:** App shows capacity analysis with recommendations

### Issue: Part 4 before Part 1
**Cause:** Sort order bug (fixed in v2.0)  
**Solution:** Update scheduler.py to sort by `(topic, part, -priority)`  
**Verification:** Check that parts are sequential in schedule

### Issue: LLM not working
**Cause:** Missing/invalid API key  
**Solution:** Set `GEMINI_API_KEY` in `.env` or Settings page  
**Fallback:** System uses template curriculum automatically

### Issue: Database corruption
**Solution:** Run `python reset_db.py` to start fresh

## 🔮 Future Enhancements

- [ ] Spaced repetition review sessions (algorithm ready, UI pending)
- [ ] Calendar integration (Google Calendar, Outlook)
- [ ] Mobile app with notifications
- [ ] Collaborative study groups
- [ ] Performance analytics dashboard
- [ ] Export to PDF/iCal
- [ ] Voice assistant integration
- [ ] Real-time schedule adjustments

## 📚 References

- Ericsson, K. A., et al. (1993). *The Role of Deliberate Practice*
- Ebbinghaus, H. (1885). *Memory: A Contribution to Experimental Psychology*
- Sweller, J. (1988). *Cognitive Load During Problem Solving*
- Walker, M. (2017). *Why We Sleep*
- Maslach, C., & Leiter, M. P. (2016). *Understanding the Burnout Experience*
- Russell & Norvig (2020). *Artificial Intelligence: A Modern Approach* (A*, CSP)

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`python test_integration.py`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request


---

**Built with ❤️ and AI principles by the Adaptive Learning Team**
