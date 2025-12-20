# backend/llm_helper.py
import os
from typing import List, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class LLMHelper:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.use_llm = False
        self.model = None

        if not self.api_key or self.api_key == "your_api_key_here":
            print("⚠️ No Gemini API key. Using fallback templates.")
            return

        try:
            genai.configure(api_key=self.api_key)

            model_list = [
                "models/gemini-2.5-flash",
                "gemini-2.5-flash",
                "models/gemini-flash-latest",
                "gemini-pro",
            ]

            for m in model_list:
                try:
                    test = genai.GenerativeModel(m)
                    # quick smoke-test
                    test.generate_content("hello")
                    self.model = test
                    self.use_llm = True
                    print(f"✅ Using Gemini model: {m}")
                    break
                except Exception:
                    continue

            if not self.use_llm:
                print("❌ Could not initialize any Gemini model. Using fallback templates.")

        except Exception as e:
            print("❌ LLM init failed:", e)
            self.use_llm = False

    # ------------------------------------------------------------------
    # MAIN API — generate curriculum with SUBTOPICS
    # ------------------------------------------------------------------
    def generate_curriculum(self, goal: str) -> List[Dict[str, Any]]:
        if not self.use_llm:
            print("⚠️ Using fallback curriculum")
            return self._fallback_curriculum(goal)

        # NOTE:
        # - we use .format(goal=goal)
        # - all literal braces in the JSON EXAMPLE are escaped as {{ and }}
        prompt = """
You are an expert curriculum designer.
Generate a detailed curriculum for the goal:

    {goal}

For EACH topic, include EXACTLY these fields:

{{
  "id": "unique_id_here",
  "title": "Topic Title",
  "prerequisites": ["list_of_ids"],
  "difficulty": 0.0 to 1.0,
  "category": "Category",
  "hours": 4,
  "description": "2 lines summary",
  "subtopics": [
    "subtopic 1",
    "subtopic 2",
    "subtopic 3",
    "subtopic 4"
  ]
}}

Rules:
- Return ONLY a JSON array.
- Each topic MUST have at least 3–8 useful subtopics.
- Subtopics must be concrete (not abstract).
- IDs must be lowercase_underscored.
""".format(
            goal=goal
        )

        try:
            response = self.model.generate_content(prompt)
            import json
            import re

            text = response.text.strip()
            # try to find a JSON array in the response
            match = re.search(r"\[[\s\S]+\]", text)
            if not match:
                raise ValueError("No JSON array found in LLM response")

            data = json.loads(match.group())

            # ensure subtopics field always exists
            cleaned: List[Dict[str, Any]] = []
            for t in data:
                if "subtopics" not in t or t["subtopics"] is None:
                    t["subtopics"] = []
                cleaned.append(t)

            return cleaned

        except Exception as e:
            print("❌ LLM error:", e)
            return self._fallback_curriculum(goal)

    # ------------------------------------------------------------------
    # FALLBACK (no LLM) — still returns subtopics field
    # ------------------------------------------------------------------
    def _fallback_curriculum(self, goal: str) -> List[Dict[str, Any]]:
        goal_lower = (goal or "").lower()

        # you can expand this later for ML, Web Dev, etc. For now a simple generic one:
        base_name = goal if goal else "Subject"
        return [
            {
                "id": "fundamentals",
                "title": f"{base_name} Fundamentals",
                "prerequisites": [],
                "difficulty": 0.3,
                "category": "Basics",
                "hours": 6,
                "description": f"Core fundamentals of {base_name}.",
                "subtopics": [
                    "Key concepts",
                    "Basic terminology",
                    "Real-world examples",
                ],
            },
            {
                "id": "core_concepts",
                "title": f"{base_name} Core Concepts",
                "prerequisites": ["fundamentals"],
                "difficulty": 0.5,
                "category": "Core",
                "hours": 8,
                "description": f"Important concepts required to work with {base_name}.",
                "subtopics": [
                    "Important sub-areas",
                    "Common patterns",
                    "Typical workflows",
                ],
            },
            {
                "id": "practice",
                "title": f"{base_name} Practice & Projects",
                "prerequisites": ["core_concepts"],
                "difficulty": 0.6,
                "category": "Practice",
                "hours": 10,
                "description": f"Hands-on practice and small projects in {base_name}.",
                "subtopics": [
                    "Mini project 1",
                    "Mini project 2",
                    "Error handling & debugging",
                ],
            },
        ]
    
    # ------------------------------------------------------------------
    # EXPLAINABILITY - Natural Language Schedule Justification
    # ------------------------------------------------------------------
    def explain_schedule_logic(self, schedule_summary: str, priority_logic: str) -> str:
        """
        Generates natural language explanation of scheduling decisions
        
        This is CRITICAL for Explainable AI - users must understand WHY
        the AI made specific decisions.
        
        Args:
            schedule_summary: "Total Sessions: 15, Focus: 5 topics, Hours: 12h"
            priority_logic: "Priority = Deadline (High) + Weakness (Medium)"
        
        Returns:
            Human-readable explanation of the schedule
        """
        if not self.use_llm:
            return (
                f"✅ Schedule optimized based on your constraints.\n\n"
                f"{schedule_summary}\n\n"
                f"**Prioritization Logic:** {priority_logic}\n\n"
                f"The AI balanced your deadline, difficulty preferences, and available time slots."
            )
        
        prompt = f"""
You are an AI Study Coach explaining your scheduling decisions to a student.

**Scheduling Logic Used:**
{priority_logic}

**Schedule Summary:**
{schedule_summary}

Explain to the student in 2-3 friendly sentences:
1. Why specific topics are prioritized the way they are
2. How this schedule fits their goals and constraints
3. One specific benefit of following this schedule

Be encouraging and specific. Reference actual numbers from the summary.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"LLM explanation failed: {e}")
            return (
                f"Schedule generated based on priority and deadline constraints.\n\n"
                f"{schedule_summary}\n\n"
                f"{priority_logic}"
            )
