"""
Topic Model - Data structure for individual learning topics
"""

from typing import List, Optional
from pydantic import BaseModel, Field

class Topic(BaseModel):
    """Represents a single learning topic in the curriculum"""
    
    id: str
    title: str
    description: str = ""
    prerequisites: List[str] = Field(default_factory=list)
    difficulty: float = Field(ge=0.0, le=1.0)  # 0.0 to 1.0
    category: str
    estimated_hours: float = Field(gt=0)
    
    # AI-computed fields
    priority: float = 0.5  # Set by reasoning engine
    completed: bool = False
    
    # Additional metadata
    resources: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'prerequisites': self.prerequisites,
            'difficulty': self.difficulty,
            'category': self.category,
            'estimated_hours': self.estimated_hours,
            'priority': self.priority,
            'completed': self.completed,
            'resources': self.resources,
            'keywords': self.keywords
        }
