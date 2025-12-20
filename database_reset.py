"""
Database Reset Script
Clears all session state and persistent data to start fresh
"""

import os
import sys
from pathlib import Path

print("=" * 80)
print("ADAPTIVE AI STUDY PLANNER - DATABASE RESET")
print("=" * 80)

# Add current directory to path
sys.path.append('.')

# Find the database file
db_path = Path("study_planner.db")

if db_path.exists():
    print(f"\n📍 Found database: {db_path.absolute()}")
    print(f"   Size: {db_path.stat().st_size / 1024:.2f} KB")
    
    # Confirm deletion
    print("\n⚠️  WARNING: This will delete ALL your data including:")
    print("   - Learning roadmaps")
    print("   - User preferences and settings")
    print("   - Completed topics and progress")
    print("   - Learning paths and schedules")
    print("   - Agent logs and transparency data")
    
    response = input("\n❓ Are you sure you want to reset? (type 'yes' to confirm): ")
    
    if response.lower() == 'yes':
        try:
            db_path.unlink()
            print("\n✅ Database deleted successfully!")
            print("   A fresh database will be created on next app launch.")
        except Exception as e:
            print(f"\n❌ Error deleting database: {str(e)}")
            sys.exit(1)
    else:
        print("\n🛑 Reset cancelled. No changes made.")
        sys.exit(0)
else:
    print(f"\n📍 No database found at {db_path.absolute()}")
    print("   Nothing to reset.")

# Also clear any backup/temp files
backup_patterns = [
    "backend/*.db-journal",
    "backend/*.db-wal",
    "backend/*.db-shm",
    "scheduler_output.json",
    "backend/csp/scheduler_output.json"
]

print("\n🔍 Checking for temporary files...")
temp_files_deleted = 0

for pattern in backup_patterns:
    for file_path in Path(".").glob(pattern):
        try:
            file_path.unlink()
            print(f"   ✅ Deleted: {file_path}")
            temp_files_deleted += 1
        except Exception as e:
            print(f"   ⚠️  Could not delete {file_path}: {str(e)}")

if temp_files_deleted > 0:
    print(f"\n✅ Cleaned up {temp_files_deleted} temporary file(s)")
else:
    print("   No temporary files found")

print("\n" + "=" * 80)
print("RESET COMPLETE")
print("=" * 80)
print("""
Next steps:
1. Restart the Streamlit app: streamlit run app.py
2. Set your new learning goal
3. Generate a fresh roadmap
4. Start learning with a clean slate!
""")
