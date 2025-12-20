"""
Ethical Safety Guard Layer
Ensures the AI system prioritizes student well-being over performance optimization

This addresses the critical question: "Should an AI push students to burnout
just because it's mathematically optimal?"
"""

from typing import List, Dict, Tuple


class EthicsGuard:
    """
    Ethical AI constraints that override optimization goals
    
    Based on research in educational psychology and cognitive load theory:
    - Maximum sustainable study time: 6-8 hours/day (Ericsson et al., 1993)
    - Break ratio for sustained focus: 15-20% of study time (Pomodoro Technique)
    - Minimum sleep protection: No studying past 11 PM
    - Weekly rest day: At least 1 day completely free
    """
    
    def __init__(self):
        # Health thresholds based on research
        self.MAX_DAILY_HOURS = 6  # Sustainable maximum
        self.OPTIMAL_DAILY_HOURS = 4  # Recommended target
        self.MIN_BREAK_RATIO = 0.15  # 15% breaks (e.g., 10 min per 50 min)
        self.OPTIMAL_BREAK_RATIO = 0.20  # 20% is ideal
        self.MAX_CONSECUTIVE_DAYS = 6  # Must have 1 rest day/week
        self.LATE_NIGHT_CUTOFF = 23  # No studying past 11 PM
        
    def check_health_constraints(self, user_model) -> Tuple[bool, List[str]]:
        """
        Validates user configuration against ethical health guidelines
        
        Returns:
            (is_safe, warnings): is_safe=False means we refuse to proceed
        """
        warnings = []
        errors = []  # Critical violations
        
        # ========================================
        # 1. BURNOUT CHECK
        # ========================================
        daily_hours = getattr(user_model, 'study_hours_per_day', 0)
        
        if daily_hours > self.MAX_DAILY_HOURS:
            errors.append(
                f"🚨 **CRITICAL: Burnout Risk Detected**\n\n"
                f"You've set {daily_hours} hours/day. Research shows this is unsustainable.\n\n"
                f"**The AI refuses to create this schedule** to protect your well-being.\n\n"
                f"**Maximum allowed:** {self.MAX_DAILY_HOURS} hours/day\n\n"
                f"**Recommended:** {self.OPTIMAL_DAILY_HOURS} hours/day for optimal retention"
            )
        elif daily_hours > self.OPTIMAL_DAILY_HOURS:
            warnings.append(
                f"⚠️ **High Study Load Warning**\n\n"
                f"{daily_hours} hours/day is achievable but challenging.\n\n"
                f"Consider reducing to {self.OPTIMAL_DAILY_HOURS} hours for better retention and lower stress."
            )
        
        # ========================================
        # 2. BREAK ADEQUACY CHECK
        # ========================================
        session_min = getattr(user_model, 'session_length', 45)
        break_min = getattr(user_model, 'break_length', 10)
        
        if session_min > 0:
            ratio = break_min / (session_min + break_min)
            
            if ratio < self.MIN_BREAK_RATIO:
                warnings.append(
                    f"⚠️ **Fatigue Risk: Insufficient Breaks**\n\n"
                    f"Your break ratio is {int(ratio*100)}% ({break_min} min break per {session_min} min session).\n\n"
                    f"**Cognitive science recommends at least {int(self.MIN_BREAK_RATIO*100)}%.**\n\n"
                    f"Suggested: {int(session_min * self.OPTIMAL_BREAK_RATIO)} minute breaks"
                )
            elif ratio < self.OPTIMAL_BREAK_RATIO:
                warnings.append(
                    f"💡 **Break Optimization Suggestion**\n\n"
                    f"Consider {int(session_min * self.OPTIMAL_BREAK_RATIO)} minute breaks "
                    f"for {session_min} minute sessions (optimal {int(self.OPTIMAL_BREAK_RATIO*100)}% ratio)"
                )
        
        # ========================================
        # 3. REST DAY CHECK
        # ========================================
        unavailable_days = getattr(user_model, 'unavailable_days', [])
        
        if len(unavailable_days) == 0:
            warnings.append(
                f"⚠️ **No Rest Days Scheduled**\n\n"
                f"You haven't set any unavailable days. Your brain needs recovery time!\n\n"
                f"**Recommendation:** Schedule at least 1 full rest day per week."
            )
        
        # ========================================
        # 4. LATE NIGHT STUDY CHECK
        # ========================================
        peak_hours = getattr(user_model, 'peak_hours', [])
        
        for slot in peak_hours:
            # Extract hour from slot like "9-12 PM"
            if "PM" in slot or "AM" in slot:
                parts = slot.split("-")
                if len(parts) == 2:
                    try:
                        # Parse end time
                        end_str = parts[1].strip()
                        end_hour = int(end_str.split()[0])
                        
                        # Adjust for PM (12-hour to 24-hour)
                        if "PM" in end_str and end_hour != 12:
                            end_hour += 12
                        elif "AM" in end_str and end_hour == 12:
                            end_hour = 0
                        
                        if end_hour >= self.LATE_NIGHT_CUTOFF:
                            warnings.append(
                                f"⚠️ **Sleep Quality Warning**\n\n"
                                f"You've selected '{slot}' as peak study time.\n\n"
                                f"Studying late (after {self.LATE_NIGHT_CUTOFF}:00) disrupts sleep and hurts retention.\n\n"
                                f"**Recommendation:** Shift to morning/afternoon hours."
                            )
                            break
                    except:
                        pass  # Parsing failed, skip
        
        # ========================================
        # FINAL VERDICT
        # ========================================
        is_safe = len(errors) == 0
        all_messages = errors + warnings
        
        return is_safe, all_messages
    
    def suggest_healthier_alternative(self, user_model) -> Dict:
        """
        Generate an ethically-optimized alternative configuration
        """
        return {
            "study_hours_per_day": self.OPTIMAL_DAILY_HOURS,
            "session_length": 50,  # Pomodoro-style
            "break_length": 10,    # 10-min breaks
            "unavailable_days": ["Sunday"],  # Force rest day
            "reasoning": (
                f"This configuration balances productivity with well-being:\n"
                f"- {self.OPTIMAL_DAILY_HOURS}h/day is sustainable long-term\n"
                f"- 50min sessions with 10min breaks (16.7% ratio)\n"
                f"- Sunday as mandatory rest day"
            )
        }
    
    def explain_ethics(self) -> str:
        """
        Explain the ethical principles guiding these constraints
        """
        return """
### 🧠 Why These Constraints Exist

The AI Study Planner prioritizes **your long-term success** over short-term gains.

**Research-Backed Principles:**

1. **Burnout Prevention** 
   - Sustained focus > 6 hours/day leads to diminishing returns
   - Quality of study matters more than quantity

2. **Spaced Learning** 
   - Rest days improve retention by 40%
   - Your brain consolidates memories during rest

3. **Cognitive Load Theory** 
   - Regular breaks prevent working memory overload
   - 15-20% break time maintains peak performance

4. **Sleep-Learning Connection** 
   - Late-night study reduces retention by up to 30%
   - Sleep is when learning becomes permanent

**The AI's Goal:** Help you learn **effectively and sustainably**, not just quickly.
        """
