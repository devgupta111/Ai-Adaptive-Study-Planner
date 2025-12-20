"""
Database Module - Robust persistence with state management and logging
Handles complex object serialization (Graph, User Model) for session continuity
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, PickleType, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import pickle
import json

Base = declarative_base()

class TopicDB(Base):
    """Database model for topics"""
    __tablename__ = 'topics'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    prerequisites = Column(PickleType)  # List stored as pickle
    difficulty = Column(Float)
    category = Column(String)
    estimated_hours = Column(Float)
    priority = Column(Float, default=0.5)
    completed = Column(Boolean, default=False)

class UserProgressDB(Base):
    """Database model for user progress"""
    __tablename__ = 'user_progress'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, default='default_user')
    topic_id = Column(String)
    completed = Column(Boolean, default=False)
    rating = Column(Float)
    completed_date = Column(String)

class StateStore(Base):
    """
    Stores complex Python objects (Graph, User Model) using pickle
    Enables session continuity across app restarts
    """
    __tablename__ = 'state_store'
    
    key = Column(String, primary_key=True)
    value = Column(PickleType)  # Pickled object
    timestamp = Column(DateTime, default=datetime.now)

class AgentLog(Base):
    """
    Transparency Layer: Logs all AI decisions for explainability
    Shows "how the system thinks"
    """
    __tablename__ = 'agent_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now)
    module = Column(String)  # "Reasoning", "CSP", "A*", "Meta", etc.
    message = Column(Text)
    details = Column(Text)  # JSON serialized details

class PersistenceManager:
    """
    Unified manager for state persistence and logging
    Handles complex object serialization and retrieval
    """
    
    def __init__(self, db_path='study_planner.db'):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    # ============================================================
    # STATE PERSISTENCE (Complex Objects)
    # ============================================================
    
    def save_state(self, key: str, obj):
        """
        Save any Python object (Graph, UserModel, etc.) to database
        Uses pickle for serialization
        """
        try:
            state = self.session.query(StateStore).filter_by(key=key).first()
            
            if state:
                state.value = obj
                state.timestamp = datetime.now()
            else:
                state = StateStore(key=key, value=obj)
                self.session.add(state)
            
            self.session.commit()
            self.log_event("Persistence", f"Saved state: {key}", f"Type: {type(obj).__name__}")
            return True
        except Exception as e:
            print(f"❌ Failed to save state '{key}': {e}")
            return False
    
    def load_state(self, key: str):
        """
        Load a previously saved Python object from database
        Returns None if not found
        """
        try:
            state = self.session.query(StateStore).filter_by(key=key).first()
            if state:
                self.log_event("Persistence", f"Loaded state: {key}", f"Timestamp: {state.timestamp}")
                return state.value
            return None
        except Exception as e:
            print(f"❌ Failed to load state '{key}': {e}")
            return None
    
    def clear_state(self, key: str):
        """Delete a saved state"""
        try:
            state = self.session.query(StateStore).filter_by(key=key).first()
            if state:
                self.session.delete(state)
                self.session.commit()
                return True
            return False
        except Exception as e:
            print(f"❌ Failed to clear state '{key}': {e}")
            return False
    
    # ============================================================
    # TRANSPARENCY LOGGING (Agent Thinking)
    # ============================================================
    
    def log_event(self, module: str, message: str, details: str = ""):
        """
        Log an AI decision/action for transparency
        
        Args:
            module: "Reasoning", "CSP", "A*", "Meta", "Ethics", etc.
            message: Brief description of action
            details: Additional context (JSON serializable)
        """
        try:
            log = AgentLog(
                module=module,
                message=message,
                details=details
            )
            self.session.add(log)
            self.session.commit()
        except Exception as e:
            print(f"⚠️ Logging failed: {e}")
    
    def get_recent_logs(self, limit: int = 10):
        """
        Retrieve recent agent logs for display
        Returns list of (module, message, timestamp) tuples
        """
        try:
            logs = self.session.query(AgentLog)\
                .order_by(AgentLog.timestamp.desc())\
                .limit(limit)\
                .all()
            
            return [(log.module, log.message, log.timestamp) for log in logs]
        except Exception as e:
            print(f"❌ Failed to retrieve logs: {e}")
            return []
    
    def clear_old_logs(self, days: int = 30):
        """Clean up logs older than specified days"""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            self.session.query(AgentLog)\
                .filter(AgentLog.timestamp < cutoff)\
                .delete()
            self.session.commit()
        except Exception as e:
            print(f"❌ Failed to clear old logs: {e}")
    
    # ============================================================
    # LEGACY METHODS (Topics/Progress)
    # ============================================================
    
    def save_topic(self, topic_data):
        """Save or update a topic"""
        topic = self.session.query(TopicDB).filter_by(id=topic_data['id']).first()
        
        if topic:
            # Update existing
            for key, value in topic_data.items():
                setattr(topic, key, value)
        else:
            # Create new
            topic = TopicDB(**topic_data)
            self.session.add(topic)
        
        self.session.commit()
    
    def get_all_topics(self):
        """Get all topics"""
        return self.session.query(TopicDB).all()
    
    def mark_complete(self, topic_id, rating=None):
        """Mark a topic as completed"""
        topic = self.session.query(TopicDB).filter_by(id=topic_id).first()
        if topic:
            topic.completed = True
            self.session.commit()


# Convenience imports
Database = PersistenceManager  # Backward compatibility
