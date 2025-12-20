"""
Reasoning Engine - Rule-Based AI Component

This module implements the REASONING LAYER of the AI agent.
It uses rules to modify topic priorities based on:
- Deadlines
- Difficulty
- User preferences
- Spaced repetition needs
"""

from typing import Dict, List
from datetime import datetime, timedelta

class ReasoningEngine:
    """
    Rule-based reasoning system for adaptive study planning.
    Applies intelligent rules to prioritize topics.
    """
    
    def __init__(self):
        self.rules = []
    
    def apply_reasoning(self, graph, user_model) -> Dict[str, float]:
        """
        Apply all reasoning rules to compute topic priorities.
        
        Returns: Dictionary mapping topic_id -> priority score (0.0 to 1.0)
        """
        priorities = {}
        
        for topic_id in graph.graph.nodes:
            topic_data = graph.get_topic_data(topic_id)
            
            # Start with base priority
            priority = 0.5
            
            # Rule 1: Deadline Urgency Rule
            priority += self._deadline_urgency_rule(user_model, graph, topic_id)
            
            # Rule 2: Difficulty Adjustment Rule
            priority += self._difficulty_rule(topic_data, user_model)
            
            # Rule 3: Prerequisite Priority Rule
            priority += self._prerequisite_rule(graph, topic_id, user_model)
            
            # Rule 4: Spaced Repetition Rule
            priority += self._spaced_repetition_rule(topic_id, user_model)
            
            # Rule 5: Learning Style Match Rule
            priority += self._learning_style_rule(topic_data, user_model)
            
            # Normalize to 0-1 range
            priority = max(0.0, min(1.0, priority))
            
            priorities[topic_id] = priority
            graph.update_priority(topic_id, priority)
        
        return priorities
    
    def _deadline_urgency_rule(self, user_model, graph, topic_id) -> float:
        """
        Rule: If deadline is approaching, increase priority of topics
        that are critical for the goal.
        """
        days_remaining = user_model.get_days_until_deadline()
        
        # More urgent if less than 30 days
        if days_remaining < 30:
            urgency = 0.3 * (1 - days_remaining / 30)
            return urgency
        
        return 0.0
    
    def _difficulty_rule(self, topic_data, user_model) -> float:
        """
        Rule: Adjust priority based on difficulty and user preference.
        
        - If user prefers gradual: prioritize easier topics
        - If user prefers advanced: prioritize harder topics
        """
        difficulty = topic_data['difficulty']
        preference = user_model.difficulty_preference
        
        if "gradually" in preference.lower():
            # Prefer easier topics early
            return -0.2 * difficulty
        elif "advanced" in preference.lower():
            # Prefer harder topics
            return 0.2 * difficulty
        
        return 0.0
    
    def _prerequisite_rule(self, graph, topic_id, user_model) -> float:
        """
        Rule: Increase priority if this topic unlocks many other topics.
        """
        # Count how many topics depend on this one
        dependents = graph.get_dependents(topic_id)
        
        if len(dependents) > 2:
            return 0.2  # High priority - unlocks many topics
        elif len(dependents) > 0:
            return 0.1  # Medium priority
        
        return 0.0
    
    def _spaced_repetition_rule(self, topic_id, user_model) -> float:
        """
        Rule: If a topic was completed >14 days ago, add review priority.
        
        This implements SPACED REPETITION for better retention.
        """
        if topic_id in user_model.completed_topics:
            # Check last study date (simplified - in real system track dates)
            # For now, add review sessions for completed topics
            return 0.15  # Moderate priority for review
        
        return 0.0
    
    def _learning_style_rule(self, topic_data, user_model) -> float:
        """
        Rule: Match topic category with user's learning style.
        """
        category = topic_data['category'].lower()
        style = user_model.learning_style.lower()
        
        # Example matching logic
        if "hands-on" in style and ("practice" in category or "project" in category):
            return 0.15
        elif "visual" in style and ("theory" in category):
            return 0.1
        
        return 0.0
    
    def explain_priority(self, topic_id, graph, user_model) -> str:
        """
        Generate human-readable explanation for why a topic has its priority.
        
        This provides EXPLAINABILITY - a key AI component.
        """
        topic_data = graph.get_topic_data(topic_id)
        priority = topic_data['priority']
        
        explanation = f"Priority for '{topic_data['title']}': {priority:.2f}\n\n"
        explanation += "Reasoning:\n"
        
        # Check each rule
        days = user_model.get_days_until_deadline()
        if days < 30:
            explanation += f"- ⏰ Deadline approaching ({days} days remaining)\n"
        
        difficulty = topic_data['difficulty']
        if difficulty > 0.7:
            explanation += f"- 🔴 High difficulty ({difficulty:.1f}) - scheduled early\n"
        elif difficulty < 0.5:
            explanation += f"- 🟢 Low difficulty ({difficulty:.1f}) - good starting point\n"
        
        dependents = graph.get_dependents(topic_id)
        if len(dependents) > 0:
            explanation += f"- 🔗 Unlocks {len(dependents)} other topics\n"
        
        if topic_id in user_model.completed_topics:
            explanation += "- 🔄 Scheduled for spaced repetition review\n"
        
        return explanation
