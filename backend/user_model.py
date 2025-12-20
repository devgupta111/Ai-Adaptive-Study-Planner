from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class UserModel(BaseModel):
    """
    Knowledge Representation: User Profile
    Stores all user preferences, constraints, and learning history.
    
    This represents the KNOWLEDGE BASE about the user.
    """
    
    # Goal
    goal: str
    deadline: datetime
    
    # Time availability
    study_hours_per_day: int
    session_length: int  # in minutes
    break_length: int    # in minutes
    peak_hours: List[str]
    unavailable_days: List[str] = Field(default_factory=list)
    # NEW: per-day available slots (day -> list of slot labels)
    available_slots: Dict[str, List[str]] = Field(default_factory=dict)
    
    # Learning preferences
    learning_style: str
    difficulty_preference: str
    
    # Learning history (adaptive components)
    completed_topics: List[str] = Field(default_factory=list)
    topic_ratings: Dict[str, float] = Field(default_factory=dict)  # topic_id -> difficulty rating by user
    study_sessions: List[Dict] = Field(default_factory=list)
    
    # Adaptive parameters
    avg_session_effectiveness: float = 1.0  # Multiplier based on performance
    preferred_time_slots: List[str] = Field(default_factory=list)

    # NEW: weaknesses + weights used by planner / reasoner
    topic_weakness: Dict[str, float] = Field(default_factory=dict)
    priority_weights: Dict[str, float] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
        extra = "allow"  # allow any extra fields safely if passed

    # ----------------- Adaptive behaviour -----------------
    def update_effectiveness(self, session_rating: float):
        """
        Update learning effectiveness based on feedback.
        This is the LEARNING component - adapting to user performance.
        """
        # Simple moving average
        self.avg_session_effectiveness = (
            0.8 * self.avg_session_effectiveness + 0.2 * session_rating
        )
    
    def mark_topic_complete(self, topic_id: str, rating: float):
        """Mark a topic as completed with difficulty rating"""
        if topic_id not in self.completed_topics:
            self.completed_topics.append(topic_id)
        self.topic_ratings[topic_id] = rating
    
    # ----------------- Availability helpers -----------------
    def get_available_hours_per_week(self) -> int:
        """
        Calculate available study hours per week.
        Prefer fine-grained available_slots if present,
        otherwise fall back to unavailable_days.
        """
        if self.available_slots:
            # days with at least one available slot
            available_days = sum(1 for d, slots in self.available_slots.items() if slots)
        else:
            # fallback: assume all days except unavailable_days are available
            available_days = 7 - len(self.unavailable_days)
        return available_days * self.study_hours_per_day
    
    def get_days_until_deadline(self) -> int:
        """Calculate remaining days until deadline"""
        if isinstance(self.deadline, datetime):
            delta = self.deadline - datetime.now()
        else:
            # if deadline somehow came as date string or date object
            try:
                from datetime import date as _date, datetime as _datetime
                if isinstance(self.deadline, _date):
                    delta = _datetime.combine(self.deadline, _datetime.min.time()) - _datetime.now()
                else:
                    delta = datetime.now() - datetime.now()
            except Exception:
                delta = datetime.now() - datetime.now()
        return max(0, delta.days)
    
    def is_peak_hour(self, time_slot: str) -> bool:
        """Check if given time slot is a peak focus hour"""
        return time_slot in self.peak_hours
    
    # ----------------- Serialization -----------------
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'goal': self.goal,
            'deadline': self.deadline.isoformat() if isinstance(self.deadline, datetime) else str(self.deadline),
            'study_hours_per_day': self.study_hours_per_day,
            'session_length': self.session_length,
            'break_length': self.break_length,
            'peak_hours': self.peak_hours,
            'unavailable_days': self.unavailable_days,
            'available_slots': self.available_slots,
            'learning_style': self.learning_style,
            'difficulty_preference': self.difficulty_preference,
            'completed_topics': self.completed_topics,
            'topic_ratings': self.topic_ratings,
            'avg_session_effectiveness': self.avg_session_effectiveness,
            'preferred_time_slots': self.preferred_time_slots,
            'topic_weakness': self.topic_weakness,
            'priority_weights': self.priority_weights,
        }
