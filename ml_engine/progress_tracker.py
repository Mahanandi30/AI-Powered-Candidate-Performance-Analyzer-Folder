import pandas as pd
import numpy as np

class ProgressTracker:
    def __init__(self):
        pass

    def analyze_progress(self, df):
        """
        Analyzes progress based on multiple attempts.
        Expects raw dataframe with 'student_id', 'course_name', 'score', 'attempt_id' (or similar).
        """
        # Ensure we have datetime or orderable attempt
        if 'attempt_timestamp' in df.columns:
            df['attempt_timestamp'] = pd.to_datetime(df['attempt_timestamp'])
            df.sort_values(by=['student_id', 'course_name', 'attempt_timestamp'], inplace=True)
        else:
            # Assume current order is chronological if no timestamp
            pass

        # Group by Student and Course
        groups = df.groupby(['student_id', 'course_name'])
        
        progress_data = []
        
        for (student_id, course_name), group in groups:
            if len(group) > 1:
                baseline = group.iloc[0]['score']
                current = group.iloc[-1]['score']
                improvement = current - baseline
                
                progress_data.append({
                    'student_id': student_id,
                    'course_name': course_name,
                    'baseline_score': baseline,
                    'current_score': current,
                    'improvement': improvement,
                    'attempts_count': len(group)
                })
        
        return pd.DataFrame(progress_data)
