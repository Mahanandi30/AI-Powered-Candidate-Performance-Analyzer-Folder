import process_data
import ml_analyzer
import pandas as pd
import os

# Define paths
base_dir = r"c:\Users\kanth\AI-Powered Candidate Performance Analyzer Folder"
scores_file = os.path.join(base_dir, "candidate_scores.csv")
feedback_file = os.path.join(base_dir, "all_students_feedback.csv")

print(f"Testing with files:\nScores: {scores_file}\nFeedback: {feedback_file}")

try:
    # 1. Process Data
    print("Running process_student_data...")
    df = process_data.process_student_data(scores_file, feedback_file)
    print("Data processed successfully.")
    print("Columns:", df.columns.tolist())
    print("Head:\n", df.head())
    
    # 2. Run ML Analysis
    print("\nRunning ML Analysis...")
    df['recommended_action'] = df.apply(ml_analyzer.recommend_courses, axis=1)
    pairings = ml_analyzer.match_mentors(df)
    
    print("ML Analysis complete.")
    print("Recommendations sample:\n", df[['name', 'recommended_action']].head())
    print("Pairings sample:\n", pairings.head())
    
    # Check if feedback is present
    if 'feedback' in df.columns:
        print("\nFeedback column verified.")
        print("Sample feedback:", df['feedback'].iloc[0])
    else:
        print("\nWARNING: Feedback column NOT found.")

    print("\nIntegration Test PASSED.")

except Exception as e:
    print(f"\nIntegration Test FAILED with error: {e}")
    import traceback
    traceback.print_exc()
