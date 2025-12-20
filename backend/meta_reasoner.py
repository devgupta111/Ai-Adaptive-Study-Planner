"""
Meta-Reasoning Layer: Applies strategic transformations to A* output
before CSP scheduling to optimize for human factors like fatigue.

This is the "thinking about thinking" layer.
"""

from typing import List, Dict
from backend.state_graph import StudyGraph


class MetaReasoner:
    """
    Meta-Reasoning: Strategic reordering of optimal path to account
    for cognitive load, fatigue, and spaced repetition.
    
    This sits BETWEEN A* (which optimizes for prerequisites/priority)
    and CSP (which optimizes for time slots).
    """
    
    def __init__(self, graph: StudyGraph):
        self.graph = graph
        
    def apply_fatigue_filter(self, ordered_topics: List[str]) -> List[str]:
        """
        Prevents scheduling back-to-back difficult topics.
        
        Strategy: If A* outputs [Hard, Hard, Easy], reorder to [Hard, Easy, Hard]
        (only if prerequisites allow).
        
        This is "Meta" because we're reasoning about the output of another
        reasoning process (A*).
        """
        if len(ordered_topics) < 3:
            return ordered_topics  # Too short to optimize
        
        reordered = []
        remaining = list(ordered_topics)
        completed = set()
        
        # Difficulty threshold
        HARD_THRESHOLD = 0.6
        
        while remaining:
            # Get topics whose prerequisites are met
            available = [
                t for t in remaining
                if self._prerequisites_met(t, completed)
            ]
            
            if not available:
                # Fallback: just take next in original order
                next_topic = remaining.pop(0)
            else:
                # Smart selection based on previous topic
                if reordered:
                    prev_topic = reordered[-1]
                    prev_difficulty = self._get_difficulty(prev_topic)
                    
                    if prev_difficulty >= HARD_THRESHOLD:
                        # Previous was hard - prefer easier topic if available
                        next_topic = self._select_easiest(available)
                    else:
                        # Previous was easy - can do hard topic
                        next_topic = self._select_hardest(available)
                else:
                    # First topic - prefer medium difficulty to warm up
                    next_topic = self._select_medium(available)
                
                remaining.remove(next_topic)
            
            reordered.append(next_topic)
            completed.add(next_topic)
        
        return reordered
    
    def apply_spaced_repetition_boost(self, ordered_topics: List[str], 
                                      completed_topics: List[str]) -> List[str]:
        """
        Insert review sessions for completed topics at strategic intervals.
        
        Spaced Repetition Schedule: Review after 1 day, 3 days, 7 days, 14 days
        """
        # TODO: Implement full spaced repetition
        # For now, return as-is
        return ordered_topics
    
    def _prerequisites_met(self, topic_id: str, completed: set) -> bool:
        """Check if all prerequisites for a topic are in completed set"""
        prereqs = self.graph.get_prerequisites(topic_id)
        return all(p in completed for p in prereqs)
    
    def _get_difficulty(self, topic_id: str) -> float:
        """Get difficulty of a topic"""
        data = self.graph.get_topic_data(topic_id)
        return data.get('difficulty', 0.5)
    
    def _select_easiest(self, topics: List[str]) -> str:
        """Select topic with lowest difficulty"""
        return min(topics, key=lambda t: self._get_difficulty(t))
    
    def _select_hardest(self, topics: List[str]) -> str:
        """Select topic with highest difficulty"""
        return max(topics, key=lambda t: self._get_difficulty(t))
    
    def _select_medium(self, topics: List[str]) -> str:
        """Select topic closest to medium difficulty (0.5)"""
        return min(topics, key=lambda t: abs(self._get_difficulty(t) - 0.5))
    
    def explain_reordering(self, original: List[str], reordered: List[str]) -> str:
        """
        Generate human-readable explanation of why topics were reordered.
        
        Explainability is critical for AI systems.
        """
        if original == reordered:
            return "No reordering needed - the A* path already optimizes cognitive load."
        
        explanation = "🧠 **Meta-Reasoning Applied**: Fatigue Filter\n\n"
        explanation += "The schedule was adjusted to prevent cognitive overload:\n\n"
        
        changes = 0
        for i in range(min(len(original), len(reordered))):
            if original[i] != reordered[i]:
                orig_title = self.graph.get_topic_data(original[i])['title']
                new_title = self.graph.get_topic_data(reordered[i])['title']
                orig_diff = self._get_difficulty(original[i])
                new_diff = self._get_difficulty(reordered[i])
                
                explanation += f"**Position {i+1}:** Changed from *{orig_title}* "
                explanation += f"(difficulty: {orig_diff:.1f}) to *{new_title}* "
                explanation += f"(difficulty: {new_diff:.1f})\n"
                changes += 1
        
        explanation += f"\n✅ Total adjustments: {changes}\n"
        explanation += "\nThis prevents back-to-back difficult topics and optimizes for sustained focus."
        
        return explanation
