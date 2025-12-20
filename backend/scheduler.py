# backend/scheduler.py

from datetime import datetime
from math import ceil
from typing import List, Dict, Any
import pprint


class SchedulerCSP:
    """
    FINAL SCHEDULER (MULTI-SESSION PER SLOT + SUBTOPICS)

    ✅ Uses user.unavailable_slots (from Set_Goal.py)
    ✅ Derives available slots internally
    ✅ Respects unavailable_days
    ✅ Allows MULTIPLE sessions inside each 3-hour slot
    ✅ Respects study_hours_per_day, session_length, break_length
    ✅ Splits topics into multiple sessions
    ✅ Uses difficulty + weakness + priority + peak hours for scoring
    ✅ Guarantees topic parts are scheduled in order (Part 1,2,3…)
    ✅ Each session gets an optional 'subtopic' string
    ✅ Returns: {weekday_name: [session_dict, ...], "_future_reviews": []}
    """

    def __init__(self, graph, user_model, ordered_topics: List[str]):
        self.graph = graph
        self.user = user_model
        self.ordered_topics = list(ordered_topics) if ordered_topics else []

        # 3-hour slots
        self.time_slots = [
            ("6-9 AM", 6, 9),
            ("9-12 PM", 9, 12),
            ("12-3 PM", 12, 15),
            ("3-6 PM", 15, 18),
            ("6-9 PM", 18, 21),
            ("9-12 AM", 21, 24),
        ]

        self.weekdays = [
            "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday"
        ]

        # slot duration in minutes (all 3 hours = 180)
        self.slot_minutes = {
            label: (end - start) * 60 for (label, start, end) in self.time_slots
        }
        self.slot_index = {label: i for i, (label, _, _) in enumerate(self.time_slots)}

        self.pp = pprint.PrettyPrinter(indent=2)

    # ------------------------------------------------------------------
    #  AVAILABLE / UNAVAILABLE  (MIRRORS Set_Goal.py)
    # ------------------------------------------------------------------
    def _available_slots(self, day: str) -> List[str]:
        """
        In Set_Goal.py you stored:
            user.unavailable_slots[day] = [list of blocked slots]

        So here we invert it to get the *available* slots.
        """
        unavailable = set(getattr(self.user, "unavailable_slots", {}).get(day, []))
        return [label for (label, _, _) in self.time_slots if label not in unavailable]

    def _day_is_fully_unavailable(self, day: str) -> bool:
        """
        A day is unavailable if:
        - it's in user.unavailable_days, OR
        - it has no available slots at all.
        """
        if day in getattr(self.user, "unavailable_days", []):
            return True
        return len(self._available_slots(day)) == 0

    def _slot_is_available(self, day: str, slot_label: str) -> bool:
        return slot_label in self._available_slots(day)

    # ------------------------------------------------------------------
    #  GRAPH / TOPIC HELPERS
    # ------------------------------------------------------------------
    def _topic_data(self, tid) -> Dict[str, Any]:
        try:
            return self.graph.get_topic_data(tid) or {}
        except Exception:
            return {}

    def _topic_title(self, tid) -> str:
        return self._topic_data(tid).get("title", str(tid))

    def _topic_difficulty(self, tid) -> float:
        return float(self._topic_data(tid).get("difficulty", 0.5))

    def _topic_hours(self, tid) -> float:
        td = self._topic_data(tid)
        return float(td.get("estimated_hours", td.get("hours", 2)))

    def _topic_priority_from_graph(self, tid) -> float:
        return float(self._topic_data(tid).get("priority", 0.5))

    def _topic_weakness(self, tid) -> float:
        return float(getattr(self.user, "topic_weakness", {}).get(tid, 0.5))

    def _slot_is_peak(self, slot_label: str) -> bool:
        return slot_label in getattr(self.user, "peak_hours", [])

    def _days_until_deadline(self) -> int:
        dl = getattr(self.user, "deadline", None)
        if isinstance(dl, datetime):
            return max(0, (dl.date() - datetime.now().date()).days)
        return 999

    def _topic_subtopics(self, tid) -> List[str]:
        """
        Get subtopics list from the graph node, if present.
        If not present, try to derive something from description.
        """
        td = self._topic_data(tid)
        subs = td.get("subtopics", None)

        if isinstance(subs, list) and subs:
            # Strip whitespace, keep non-empty
            cleaned = [s.strip() for s in subs if isinstance(s, str) and s.strip()]
            if cleaned:
                return cleaned

        # Fallback: try to split description into pseudo-subtopics
        desc = td.get("description", "")
        if isinstance(desc, str) and desc.strip():
            # Split on '.' or ',' for rough bullets
            import re
            chunks = re.split(r'[.,;]+', desc)
            cleaned = [c.strip() for c in chunks if c.strip()]
            return cleaned

        return []

    # ------------------------------------------------------------------
    #  SPLITTING TOPICS INTO SESSIONS
    # ------------------------------------------------------------------
    def _split_topic_into_sessions(self, topic_id: str, session_len_min: int) -> List[Dict[str, Any]]:
        """
        Split each topic into multiple study sessions of approx session_len_min.
        """
        total_minutes = max(1, int(round(self._topic_hours(topic_id) * 60)))
        parts = max(1, ceil(total_minutes / session_len_min))

        sessions = []
        minutes_left = total_minutes

        for i in range(parts):
            if i < parts - 1:
                duration = session_len_min
            else:
                duration = minutes_left

            if duration <= 0:
                duration = session_len_min

            sessions.append(
                {
                    "parent_topic": topic_id,
                    "part_index": i + 1,
                    "total_parts": parts,
                    "minutes": int(duration),
                }
            )
            minutes_left -= duration

        return sessions

    # ------------------------------------------------------------------
    #  SCORING FUNCTION (used when selecting day+slot)
    # ------------------------------------------------------------------
    def _score_slot(
        self,
        session_meta: Dict[str, Any],
        day: str,
        slot_label: str,
        remaining_today: int,
        remaining_in_slot: int,
    ) -> float:
        """
        Higher score = better placement.
        - difficulty & weakness
        - graph priority
        - peak vs non-peak
        - smaller days_until_deadline
        - earlier slots get a small bonus (so we fill 6–9, then 9–12, etc.)
        """
        tid = session_meta["parent_topic"]
        diff = self._topic_difficulty(tid)
        prio = self._topic_priority_from_graph(tid)
        weak = self._topic_weakness(tid)
        days_left = self._days_until_deadline()

        score = 0.0

        # Base: give some weight for having remaining space
        score += remaining_today / 5.0
        score += remaining_in_slot / 5.0

        # Graph priority & weakness
        score += prio * 100.0
        score += weak * 80.0

        # Difficulty – prefer hard topics in good slots
        if self._slot_is_peak(slot_label):
            score += diff * 120.0
        else:
            score += diff * 40.0

        # Deadline urgency
        if days_left < 30:
            urgency = (30 - days_left) / 30.0
            score += urgency * 120.0

        # Small bonus for earlier slots so they fill first
        slot_idx = self.slot_index.get(slot_label, 0)
        score -= slot_idx * 5.0  # earlier -> less penalty -> higher score

        return score

    # ------------------------------------------------------------------
    #  MAIN SCHEDULING LOOP
    # ------------------------------------------------------------------
    def generate_schedule(self) -> Dict[str, Any]:
        """
        Core CSP-style greedy scheduler.

        It will:
        - Expand each topic into multiple sessions
        - For each session, search over all days & slots
        - A slot can hold MANY sessions as long as:
            * slot_capacity (3h) is not exceeded
            * study_hours_per_day is not exceeded
            * max_sessions_per_day is not exceeded
        - Select the best (day, slot) by score
        """

        # basic config
        study_hours = int(getattr(self.user, "study_hours_per_day", 3))
        daily_limit = study_hours * 60  # minutes per day
        session_len = int(getattr(self.user, "session_length", 45))
        break_len = int(getattr(self.user, "break_length", 10))

        # Allow more sessions per day for better topic splitting
        # Respects BOTH daily_limit and slot capacity (180 min each)
        theoretical = max(1, daily_limit // (session_len + break_len))
        
        # Don't artificially limit - let daily_limit and slot capacity be the real constraints
        max_sessions_per_day = theoretical  # Removed artificial cap
        
        print(f"\n🔧 Scheduler Config:")
        print(f"   Study hours/day: {study_hours}h ({daily_limit} min)")
        print(f"   Session: {session_len}min + Break: {break_len}min = {session_len + break_len}min")
        print(f"   Max sessions/day: {max_sessions_per_day}")

        # Calculate how many weeks we have until deadline
        days_until = self._days_until_deadline()
        weeks_available = max(1, (days_until + 6) // 7)  # Round up
        
        # Multi-week schedule: {week_num: {day: [sessions]}}
        # We'll generate up to weeks_available weeks
        schedule: Dict[str, Any] = {}
        for week in range(1, weeks_available + 1):
            for day in self.weekdays:
                schedule[f"Week {week} - {day}"] = []
        
        # Also maintain a simple weekly view for compatibility
        current_week_schedule = {d: [] for d in self.weekdays}
        
        # ✅ CRITICAL: Track topics that couldn't be scheduled
        dropped_topics = []
        dropped_parts = []  # (topic_id, part_index, reason)
        
        print(f"   Planning for {weeks_available} week(s) until deadline")

        # --------------------------------------------------
        # Expand topics into sessions (+ assign subtopics)
        # --------------------------------------------------
        expanded: List[Dict[str, Any]] = []

        for tid in self.ordered_topics:
            if tid in getattr(self.user, "completed_topics", []):
                continue

            parts = self._split_topic_into_sessions(tid, session_len)
            base_title = self._topic_title(tid)
            subtopics = self._topic_subtopics(tid)  # list[str]

            total_parts = len(parts)
            n_sub = len(subtopics)

            # precompute chunk size for mapping subtopics to parts
            chunk_size = max(1, ceil(n_sub / total_parts)) if n_sub > 0 else 0

            for p in parts:
                # ----- title -----
                if total_parts == 1:
                    title = base_title
                else:
                    title = f"{base_title} (Part {p['part_index']}/{total_parts})"

                # ----- subtopic text for this part -----
                subtopic_text = None
                if n_sub > 0:
                    # Map part_index → slice of subtopics
                    idx0 = (p["part_index"] - 1) * chunk_size
                    idx1 = min(idx0 + chunk_size, n_sub)
                    chosen = subtopics[idx0:idx1] if idx0 < n_sub else []
                    if chosen:
                        subtopic_text = ", ".join(chosen)

                # fallback: if still none, maybe use description chunk later via _topic_subtopics

                p["title"] = title
                p["subtopic"] = subtopic_text  # may be None
                p["difficulty"] = self._topic_difficulty(tid)
                p["priority_graph"] = self._topic_priority_from_graph(tid)
                p["weakness"] = self._topic_weakness(tid)
                expanded.append(p)

        # ------------- CRITICAL FIX: SORT BY TOPIC+PART FIRST, THEN PRIORITY ----------
        # This ensures Part 1 always comes before Part 2 for the same topic
        # Otherwise high-priority topics get all parts sorted to top, and if Part 1
        # can't fit early, Part 2/3/4 might get scheduled before Part 1
        def _priority_score(s: Dict[str, Any]) -> float:
            return (
                s["priority_graph"] * 100.0
                + s["weakness"] * 80.0
                + s["difficulty"] * 60.0
            )

        expanded.sort(
            key=lambda s: (
                s["parent_topic"],             # group same topic together FIRST
                s["part_index"],               # Part 1,2,3… in order within topic
                -_priority_score(s),           # higher importance first within same part
            )
        )

        # --------------------------------------------------
        # Placement loop - Multi-week scheduling with retry logic
        # --------------------------------------------------
        placed_parts = set()  # (topic_id, part_index)
        unplaced_sessions = list(expanded)  # Sessions to place
        max_passes = 10  # Prevent infinite loops
        
        for pass_num in range(max_passes):
            placed_in_this_pass = 0
            still_unplaced = []
            
            for session_meta in unplaced_sessions:
                tid = session_meta["parent_topic"]
                part = session_meta["part_index"]
                duration = session_meta["minutes"]

                # 🔒 CRITICAL: Ensure sequential part placement
                # Part 2 cannot be scheduled until Part 1 is placed
                if part > 1 and (tid, part - 1) not in placed_parts:
                    # Keep in queue for next pass (previous part might get placed)
                    still_unplaced.append(session_meta)
                    continue

                best_choice = None
                best_score = -1e12

                # Search across all weeks and days
                for week in range(1, weeks_available + 1):
                    for day in self.weekdays:
                        week_day_key = f"Week {week} - {day}"
                        
                        if self._day_is_fully_unavailable(day):
                            continue

                        day_list = schedule[week_day_key]

                        # Daily time constraint: respect study_hours_per_day
                        # BUT if user has multiple available slots, they can use them all up to the limit
                        used_today = sum(s["duration"] + s["break_after"] for s in day_list)
                        remaining_today = daily_limit - used_today
                        
                        # Allow scheduling if there's ANY remaining time today
                        if remaining_today <= 0:
                            continue

                        # Allow same topic multiple times per day (for multi-part topics)
                        # Only restrict: don't schedule same PART twice
                        if any(s["topic_id"] == tid and s.get("part_index") == part for s in day_list):
                            continue

                        # search over slots in this day
                        for slot_label, _start, _end in self.time_slots:
                            if not self._slot_is_available(day, slot_label):
                                continue

                            # compute remaining capacity in this slot
                            used_in_slot = sum(
                                s["duration"] + s["break_after"]
                                for s in day_list
                                if s["time"] == slot_label
                            )
                            capacity = self.slot_minutes[slot_label]
                            remaining_in_slot = capacity - used_in_slot

                            # Can we fit this session in this slot?
                            # Check BOTH slot capacity AND remaining daily budget
                            session_needs = duration + break_len
                            
                            if remaining_in_slot < session_needs:
                                continue
                            
                            if remaining_today < session_needs:
                                continue

                            score = self._score_slot(
                                session_meta,
                                day,
                                slot_label,
                                remaining_today,
                                remaining_in_slot,
                            )

                            if score > best_score:
                                best_score = score
                                best_choice = (week, day, slot_label)

                # actually place, if we found any valid week+day+slot
                if best_choice is not None:
                    week, day, slot_label = best_choice
                    week_day_key = f"Week {week} - {day}"
                    
                    session_obj = {
                        "topic_id": tid,
                        "title": session_meta["title"],
                        "subtopic": session_meta.get("subtopic"),
                        "duration": duration,
                        "break_after": break_len,
                        "time": slot_label,
                        "is_peak": self._slot_is_peak(slot_label),
                        "difficulty": session_meta["difficulty"],
                        "part_index": part,
                        "total_parts": session_meta["total_parts"],
                        "week": week,
                    }
                    
                    schedule[week_day_key].append(session_obj)
                    placed_parts.add((tid, part))
                    placed_in_this_pass += 1
                    
                    # Also add to Week 1 simple schedule for backwards compatibility
                    if week == 1:
                        if day not in current_week_schedule:
                            current_week_schedule[day] = []
                        current_week_schedule[day].append(session_obj)
                else:
                    # Keep in queue for next pass
                    still_unplaced.append(session_meta)
            
            # Update queue for next pass
            unplaced_sessions = still_unplaced
            
            # If nothing was placed this pass, we're done trying
            if placed_in_this_pass == 0:
                break
        
        # After all passes, anything still unplaced goes to dropped list
        for session_meta in unplaced_sessions:
            tid = session_meta["parent_topic"]
            part = session_meta["part_index"]
            
            reason = "No available time slots found"
            if part > 1 and (tid, part - 1) not in placed_parts:
                reason = f"Part {part-1} was not scheduled (prerequisite for this part)"
            
            dropped_parts.append({
                "topic_id": tid,
                "title": session_meta["title"],
                "part": part,
                "total_parts": session_meta["total_parts"],
                "reason": reason
            })
            
            # If Part 1 failed, mark entire topic as dropped
            if part == 1 and tid not in [d["topic_id"] for d in dropped_topics]:
                dropped_topics.append({
                    "topic_id": tid,
                    "title": self._topic_title(tid),
                    "hours": self._topic_hours(tid),
                    "reason": "Cannot fit in available time slots"
                })

        # --------------------------------------------------
        # Sort sessions in each week-day by slot order (and part_index)
        # --------------------------------------------------
        slot_order = [label for (label, _, _) in self.time_slots]

        total_scheduled = sum(len(sessions) for key, sessions in schedule.items() if isinstance(sessions, list))
        total_attempted = len(expanded)
        
        print(f"\n📊 Scheduling Results:")
        print(f"   Total sessions attempted: {total_attempted}")
        print(f"   Successfully scheduled: {total_scheduled}")
        print(f"   Dropped: {len(dropped_parts)} parts from {len(dropped_topics)} topics")

        # Sort each week-day
        for week in range(1, weeks_available + 1):
            for day in self.weekdays:
                week_day_key = f"Week {week} - {day}"
                
                if self._day_is_fully_unavailable(day):
                    schedule[week_day_key] = "UNAVAILABLE"
                    continue

                day_list = schedule[week_day_key]
                day_list.sort(
                    key=lambda s: (
                        slot_order.index(s["time"]) if s.get("time") in slot_order else 999,
                        s.get("part_index", 0),
                    )
                )
                
                if day_list and week == 1:  # Only print Week 1 summary
                    total_min = sum(s["duration"] + s["break_after"] for s in day_list)
                    print(f"   Week 1 - {day}: {len(day_list)} sessions ({total_min}min)")

        # Add metadata
        schedule["_weeks_available"] = weeks_available
        schedule["_future_reviews"] = []
        schedule["_dropped_topics"] = dropped_topics
        schedule["_dropped_parts"] = dropped_parts
        schedule["_current_week_schedule"] = current_week_schedule  # For backwards compatibility

        # Debug (optional) - only print Week 1 to avoid console spam
        print("=== SchedulerCSP WEEK 1 PREVIEW ===")
        week1_preview = {day: schedule.get(f"Week 1 - {day}", []) for day in self.weekdays}
        self.pp.pprint(week1_preview)
        
        if dropped_topics:
            print(f"\n⚠️  WARNING: {len(dropped_topics)} topics could not be scheduled:")
            for dt in dropped_topics:
                print(f"   - {dt['title']} ({dt['hours']}h): {dt['reason']}")

        return schedule
