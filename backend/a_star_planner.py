"""
A* Search Algorithm for Optimal Learning Path

This module implements the A* SEARCH algorithm to find the optimal
order of topics to study, considering:
- Prerequisites (hard constraints)
- Difficulty
- Time estimates
- Priorities from reasoning engine
"""

import heapq
from typing import List, Dict, Tuple
import networkx as nx

class AStarPlanner:
    """
    A* Search implementation for finding optimal learning path.
    
    State Space:
    - State: Set of completed topics
    - Actions: Study an available topic (prerequisites met)
    - Goal: All topics completed
    """
    
    def __init__(self, graph, user_model):
        self.graph = graph
        self.user_model = user_model
    
    def find_optimal_path(self) -> List[str]:
        """
        Find optimal learning path using A* search.
        
        Returns: Ordered list of topic IDs
        """
        # Get all topics
        all_topics = set(self.graph.graph.nodes)
        
        # Initial state: no topics completed
        initial_state = frozenset()
        
        # Goal state: all topics completed
        goal_state = frozenset(all_topics)
        
        # Priority queue: (f_score, g_score, state, path)
        open_set = []
        heapq.heappush(open_set, (
            self._heuristic(initial_state, goal_state),
            0,
            initial_state,
            []
        ))
        
        # Track visited states
        visited = set()
        
        # Best g_score for each state
        g_scores = {initial_state: 0}
        
        while open_set:
            f_score, g_score, current_state, path = heapq.heappop(open_set)
            
            # Check if goal reached
            if current_state == goal_state:
                return path
            
            # Skip if already visited
            if current_state in visited:
                continue
            
            visited.add(current_state)
            
            # Get available topics (prerequisites met)
            completed_list = list(current_state)
            available = self.graph.get_available_topics(completed_list)
            
            # Try each available topic
            for topic_id in available:
                # New state after completing this topic
                new_state = frozenset(current_state | {topic_id})
                
                # Calculate cost to reach new state
                new_g_score = g_score + self._action_cost(topic_id)
                
                # Only proceed if this is a better path
                if new_state not in g_scores or new_g_score < g_scores[new_state]:
                    g_scores[new_state] = new_g_score
                    
                    # Calculate f_score = g_score + heuristic
                    new_f_score = new_g_score + self._heuristic(new_state, goal_state)
                    
                    # Add to priority queue
                    heapq.heappush(open_set, (
                        new_f_score,
                        new_g_score,
                        new_state,
                        path + [topic_id]
                    ))
        
        # Fallback: return topological sort if A* fails
        return self.graph.get_learning_path()
    
    def _action_cost(self, topic_id: str) -> float:
        """
        Calculate cost of studying a topic.
        
        Cost function considers:
        - Time required
        - Difficulty
        - Priority (from reasoning engine)
        """
        topic_data = self.graph.get_topic_data(topic_id)
        
        # Base cost: estimated hours
        time_cost = topic_data['estimated_hours']
        
        # Difficulty cost: harder topics have higher cost
        difficulty_cost = topic_data['difficulty'] * 10
        
        # Priority cost: high priority topics have LOWER cost (prioritized)
        priority_cost = (1.0 - topic_data['priority']) * 5
        
        # Total cost
        total_cost = time_cost + difficulty_cost + priority_cost
        
        return total_cost
    
    def _heuristic(self, current_state: frozenset, goal_state: frozenset) -> float:
        """
        Heuristic function: estimate cost to reach goal from current state.
        
        This makes the search admissible (never overestimates).
        """
        # Topics remaining
        remaining = goal_state - current_state
        
        if not remaining:
            return 0
        
        # Estimate: sum of minimum costs for remaining topics
        total_estimate = 0
        
        for topic_id in remaining:
            topic_data = self.graph.get_topic_data(topic_id)
            
            # Optimistic estimate: just time required
            total_estimate += topic_data['estimated_hours']
        
        return total_estimate
    
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
        explanation += "The algorithm minimized total cost while respecting prerequisites."
        
        return explanation
