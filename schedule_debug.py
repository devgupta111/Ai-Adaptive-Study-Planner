"""Debug script to understand scheduling constraints"""
import sys
sys.path.append('.')
from backend.db import PersistenceManager
from datetime import date

pm = PersistenceManager()
user_data = pm.load_state('user_data')
learning_path = pm.load_state('learning_path')
graph = pm.load_state('graph')

if not user_data:
    print('No user data found')
    sys.exit(1)

print('=' * 60)
print('CURRENT SETTINGS')
print('=' * 60)

study_hours = user_data.get('study_hours_per_day', 3)
session_len = user_data.get('session_length', 45)
break_len = user_data.get('break_length', 10)
deadline = user_data.get('deadline', date.today())

print(f'Study hours/day: {study_hours}h = {study_hours * 60} minutes')
print(f'Session length: {session_len} min')
print(f'Break length: {break_len} min')
print(f'Deadline: {deadline}')

# Calculate daily capacity
daily_limit = study_hours * 60
session_with_break = session_len + break_len
theoretical_sessions = daily_limit // session_with_break
max_sessions = min(8, max(3, theoretical_sessions))

print(f'\nDaily limit: {daily_limit} minutes')
print(f'Session + break: {session_with_break} minutes')
print(f'Theoretical sessions/day: {theoretical_sessions}')
print(f'Max sessions/day (capped): {max_sessions}')

print('\n' + '=' * 60)
print('AVAILABLE TIME SLOTS')
print('=' * 60)

all_slots = ['6-9 AM', '9-12 PM', '12-3 PM', '3-6 PM', '6-9 PM', '9-12 AM']
weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

unavail_slots = user_data.get('unavailable_slots', {})
unavail_days = user_data.get('unavailable_days', [])

total_slots = 0
available_days = 0

for day in weekdays:
    if day in unavail_days:
        print(f'{day:12} FULLY UNAVAILABLE')
    else:
        unavail = set(unavail_slots.get(day, []))
        avail = [s for s in all_slots if s not in unavail]
        total_slots += len(avail)
        if avail:
            available_days += 1
        print(f'{day:12} {len(avail)}/6 slots: {", ".join(avail) if avail else "NONE"}')

print(f'\nTotal available slots across week: {total_slots}')
print(f'Total available slot-hours: {total_slots * 3}h (if using full slots)')
print(f'Days with any availability: {available_days}')

# Calculate actual capacity
days_until = (deadline - date.today()).days
actual_capacity = days_until * study_hours
print(f'\nDays until deadline: {days_until}')
print(f'Total capacity: {days_until} days × {study_hours}h = {actual_capacity}h')

print('\n' + '=' * 60)
print('TOPIC REQUIREMENTS')
print('=' * 60)

if graph and learning_path:
    total_hours = 0
    topics_count = len(learning_path)
    
    print(f'Total topics: {topics_count}')
    print(f'\nFirst 10 topics:')
    
    for i, topic_id in enumerate(learning_path[:10], 1):
        data = graph.get_topic_data(topic_id)
        hours = data.get('estimated_hours', 2)
        total_hours += hours
        sessions_needed = (hours * 60) // session_len
        print(f'{i:2}. {data["title"]:40} {hours:4.1f}h ({sessions_needed:2.0f} sessions)')
    
    # Calculate total for all topics
    total_hours = sum(graph.get_topic_data(t).get('estimated_hours', 2) for t in learning_path)
    print(f'\nTotal hours needed: {total_hours:.1f}h')
    print(f'Capacity vs Need: {actual_capacity:.1f}h available vs {total_hours:.1f}h needed')
    
    if actual_capacity < total_hours:
        deficit = total_hours - actual_capacity
        print(f'⚠️  DEFICIT: {deficit:.1f}h SHORT')
        print(f'    Need to add {deficit / study_hours:.1f} more days')
    else:
        print(f'✅ Sufficient time (surplus: {actual_capacity - total_hours:.1f}h)')

print('\n' + '=' * 60)
print('SCHEDULING CONSTRAINTS ANALYSIS')
print('=' * 60)

# Per-slot capacity
print(f'\nEach slot = 180 minutes (3 hours)')
print(f'With {session_len}min sessions + {break_len}min breaks:')
print(f'  Max sessions per 3h slot: {180 // session_with_break}')
print(f'  Wasted time per slot: {180 % session_with_break} minutes')

# Daily constraints
print(f'\nDaily constraints:')
print(f'  Study limit: {daily_limit} minutes')
print(f'  Max sessions: {max_sessions}')
print(f'  Total session time: {max_sessions * session_with_break} minutes')

if max_sessions * session_with_break > daily_limit:
    print(f'  ⚠️  Sessions would exceed daily limit!')
    actual_daily_sessions = daily_limit // session_with_break
    print(f'  Actual achievable: {actual_daily_sessions} sessions/day')
