import networkx as nx
from typing import List, Dict, Optional


class StudyGraph:
    """
    State Space representation for the Adaptive Study Planner.
    Each topic is a node. Edges represent prerequisites.
    Includes subtopics support.
    """

    def __init__(self):
        self.graph = nx.DiGraph()

    # -----------------------------------------------------------
    # ADD TOPIC
    # -----------------------------------------------------------
    def add_topic(
        self,
        topic_id: str,
        title: str,
        prerequisites: List[str],
        difficulty: float,
        category: str,
        estimated_hours: float,
        description: str = "",
        subtopics: Optional[List[str]] = None,
    ):
        """Add a topic node (with subtopics) into graph"""

        self.graph.add_node(
            topic_id,
            title=title,
            prerequisites=prerequisites,
            difficulty=difficulty,
            category=category,
            estimated_hours=estimated_hours,
            description=description,
            subtopics=subtopics or [],
            completed=False,
            priority=0.5,
        )

        # Add prerequisite edges
        for prereq in prerequisites:
            if prereq in self.graph.nodes:
                self.graph.add_edge(prereq, topic_id)

    # -----------------------------------------------------------
    # AVAILABLE TOPICS (A* PLANNER NEEDS THIS)
    # -----------------------------------------------------------
    def get_available_topics(self, completed_topics: List[str]) -> List[str]:
        """
        Topics whose prerequisites are all complete.
        This function **must exist** because A* calls it.
        """
        available = []
        for node in self.graph.nodes:
            if node in completed_topics:
                continue

            prereqs = list(self.graph.predecessors(node))

            if all(p in completed_topics for p in prereqs):
                available.append(node)

        return available

    # -----------------------------------------------------------
    # BASIC ACCESSORS
    # -----------------------------------------------------------
    def get_topic_data(self, topic_id: str) -> Dict:
        return self.graph.nodes.get(topic_id, {})

    def get_prerequisites(self, topic_id: str) -> List[str]:
        return list(self.graph.predecessors(topic_id))

    def get_dependents(self, topic_id: str) -> List[str]:
        return list(self.graph.successors(topic_id))

    # -----------------------------------------------------------
    # TOPOLOGICAL ORDERING (fallback ordering)
    # -----------------------------------------------------------
    def get_learning_path(self) -> List[str]:
        try:
            return list(nx.topological_sort(self.graph))
        except nx.NetworkXError:
            return list(self.graph.nodes)

    # -----------------------------------------------------------
    # PRIORITY UPDATE
    # -----------------------------------------------------------
    def update_priority(self, topic_id: str, priority: float):
        if topic_id in self.graph.nodes:
            self.graph.nodes[topic_id]["priority"] = priority
    
    def recalculate_priorities(self, user_model):
        """
        Active Knowledge Representation: Recalculate all topic priorities
        based on current user model (deadlines, learning style, etc.)
        
        This makes the graph "alive" - it updates its own state.
        """
        from backend.reasoner import ReasoningEngine
        
        reasoner = ReasoningEngine()
        priorities = reasoner.apply_reasoning(self, user_model)
        
        return priorities  # Dictionary of topic_id -> priority

    # -----------------------------------------------------------
    # VISUALIZATION SUPPORT
    # -----------------------------------------------------------
    def visualize(self):
        nodes = []
        edges = []

        for node_id in self.graph.nodes:
            d = self.graph.nodes[node_id]
            nodes.append(
                {
                    "id": node_id,
                    "label": d["title"],
                    "difficulty": d["difficulty"],
                    "category": d["category"],
                    "hours": d["estimated_hours"],
                    "subtopics": d.get("subtopics", []),
                }
            )

        for e in self.graph.edges:
            edges.append({"source": e[0], "target": e[1]})

        return {"nodes": nodes, "edges": edges}

    # -----------------------------------------------------------
    # HOURS TRACKING
    # -----------------------------------------------------------
    def get_total_hours(self) -> float:
        return sum(self.graph.nodes[n]["estimated_hours"] for n in self.graph.nodes)

    def get_completed_hours(self, completed_topics: List[str]) -> float:
        return sum(
            self.graph.nodes[n]["estimated_hours"]
            for n in completed_topics
            if n in self.graph.nodes
        )
