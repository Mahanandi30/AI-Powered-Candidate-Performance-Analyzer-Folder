import process_data
import ml_analyzer
import pandas as pd
import os
import shutil

# Define paths
base_dir = r"c:\Users\kanth\AI-Powered Candidate Performance Analyzer Folder"
scores_file = os.path.join(base_dir, "candidate_scores.csv")
feedback_file = os.path.join(base_dir, "all_students_feedback.csv")
pairings_file = os.path.join(base_dir, "pairings.csv")

# Create a simulated upload folder
upload_dir = os.path.join(base_dir, "uploads_test")
if not os.path.exists(upload_dir):
    os.makedirs(upload_dir)

print(f"Testing with files:\nScores: {scores_file}\nFeedback: {feedback_file}\nPairings: {pairings_file}")

try:
    # 1. Process Data (Scores + Feedback)
    print("\n[1] Processing Student Data...")
    df = process_data.process_student_data(scores_file, feedback_file)
    print("Columns:", df.columns.tolist())
    
    # 2. Add Recommendations
    print("\n[2] Generating Recommendations...")
    df['recommended_action'] = df.apply(ml_analyzer.recommend_courses, axis=1)
    
    # 3. Simulate Pairings File Upload Logic
    print("\n[3] Testing Pairings File Integration...")
    if os.path.exists(pairings_file):
        print("User provided pairings.csv found.")
        pairings_df = process_data.load_data(pairings_file)
        
        # Rename logic from app.py
        cols = pairings_df.columns.str.lower()
        pairings_df.columns = cols
        
        rename_map = {}
        if 'course_id' in cols and 'course' not in cols: rename_map['course_id'] = 'course'
        if 'weak_student_name' in cols: rename_map['weak_student_name'] = 'mentee_name'
        if 'mentor_name' in cols: rename_map['mentor_name'] = 'mentor_name'
        if 'mentee' in cols: rename_map['mentee'] = 'mentee_name'
        if 'mentor' in cols: rename_map['mentor'] = 'mentor_name'
            
        pairings_df.rename(columns=rename_map, inplace=True)
        print("Renamed Columns:", pairings_df.columns.tolist())
        
        # Verify columns required for dashboard: course, mentor_name, mentee_name
        required = {'course', 'mentor_name', 'mentee_name'}
        current = set(pairings_df.columns)
        if required.issubset(current):
             print("SUCCESS: Pairings file has all required columns for dashboard.")
             print(pairings_df.head(2))
        else:
             print(f"FAILURE: Pairings file missing columns. Found: {current}, Expected: {required}")
    else:
        print("SKIPPING: pairings.csv not found for test.")

    print("\nIntegration Test 2 PASSED.")

except Exception as e:
    print(f"\nIntegration Test 2 FAILED with error: {e}")
    import traceback
    traceback.print_exc()
