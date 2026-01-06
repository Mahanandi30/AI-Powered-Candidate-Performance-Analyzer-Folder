from ml_engine.data_processor import DataProcessor
from ml_engine.performance_analyzer import PerformanceAnalyzer
from ml_engine.recommender import CourseRecommender
from ml_engine.mentor_matcher import MentorMatcher
import os
import pandas as pd

# Define paths
base_dir = r"c:\Users\kanth\AI-Powered Candidate Performance Analyzer Folder"
scores_file = os.path.join(base_dir, "candidate_scores.csv")
feedback_file = os.path.join(base_dir, "all_students_feedback.csv")

print("Testing New Architecture...")

try:
    # 1. Initialize Engines
    dp = DataProcessor()
    pa = PerformanceAnalyzer()
    cr = CourseRecommender()
    mm = MentorMatcher()
    print("[OK] Engines Initialized")

    # 2. Process Data
    print("\n--- Testing Data Processing ---")
    if os.path.exists(scores_file):
        df = dp.process_student_data(scores_file, feedback_file)
        print("Data Processed. Shape:", df.shape)
        print("Columns:", df.columns.tolist())
    else:
        print("Scores file not found, skipping data test.")
        df = pd.DataFrame([{'name': 'Test', 'best_score': 50, 'course_name': 'Python', 'student_id': 1}])

    # 3. Analyze Performance
    print("\n--- Testing Performance Analysis ---")
    if 'performance' not in df.columns:
        df['performance'] = df['best_score'].apply(pa.classify_performance)
    print("Performance sample:", df[['best_score', 'performance']].head(2).to_dict('records'))

    # 4. Recommend
    print("\n--- Testing Recommendations ---")
    df['recommended_action'] = df.apply(cr.recommend_courses, axis=1)
    print("Recommendation sample:", df[['performance', 'recommended_action']].head(2).to_dict('records'))

    # 5. Match Mentors
    print("\n--- Testing Mentor Matching ---")
    # Force some data to ensure matching logic runs if file is empty
    if len(df) < 2:
        extra = pd.DataFrame([
            {'name': 'Mentor1', 'performance': 'High', 'course_name': 'Python', 'email': 'm@test.com'},
            {'name': 'Mentee1', 'performance': 'Poor', 'course_name': 'Python', 'email': 's@test.com'}
        ])
        df = pd.concat([df, extra], ignore_index=True)
        
    pairs = mm.match_mentors_simple(df)
    print("Pairs Generated:", len(pairs))
    if not pairs.empty:
        print(pairs.head(2))

    print("\n[SUCCESS] New Architecture Verification Passed.")

except Exception as e:
    print(f"\n[FAILURE] Error: {e}")
    import traceback
    traceback.print_exc()
