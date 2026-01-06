    import pandas as pd
import numpy as np
from sklearn.cluster import KMeans

class PerformanceAnalyzer:
    def __init__(self):
        self.thresholds = {'High': 80, 'Medium': 60, 'Poor': 0}
    
    def classify_performance(self, score):
        """
        Classifies performance based on score (Rule-based default).
        """
        if score < 60:
            return 'Poor'
        elif score <= 80:
            return 'Medium'
        else:
            return 'High'

    def classify_students_kmeans(self, df, n_clusters=3):
        """
        Advanced: Uses K-Means clustering to classify students if enough data exists.
        Expects a dataframe with 'best_score' or 'average_score'.
        """
        if len(df) < n_clusters:
            # Fallback to rule-based if not enough data points
             return df['best_score'].apply(self.classify_performance)
             
        X = df[['best_score']].values
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        df['cluster'] = kmeans.fit_predict(X)
        
        # Map clusters to labels based on centroid limits
        centroids = kmeans.cluster_centers_
        sorted_idx = np.argsort(centroids.flatten())
        
        # Assuming 3 clusters: Lowest centroid -> Poor, Middle -> Medium, Highest -> High
        cluster_map = {
            sorted_idx[0]: 'Poor',
            sorted_idx[1]: 'Medium',
            sorted_idx[2]: 'High'
        }
        
        return df['cluster'].map(cluster_map)

    def analyze_strengths_weaknesses(self, student_history_df):
        """
        Analyze logic to return insights for a single student.
        Expects a DataFrame of that student's attempts with 'course_name' and 'score'.
        """
        if student_history_df.empty or 'course_name' not in student_history_df.columns or 'score' not in student_history_df.columns:
            return {'strengths': [], 'weaknesses': []}
            
        # Sort by timestamp if available to get true latest score
        if 'attempt_timestamp' in student_history_df.columns:
            student_history_df['attempt_timestamp'] = pd.to_datetime(student_history_df['attempt_timestamp'], errors='coerce')
            student_history_df = student_history_df.sort_values('attempt_timestamp')

        # Get latest score per course
        course_performance = student_history_df.groupby('course_name')['score'].last()
        
        # Notebook Logic: >= 80 Strong, < 50 Weak (Recommendation trigger)
        strengths = course_performance[course_performance >= 80].index.tolist()
        weaknesses = course_performance[course_performance < 50].index.tolist()
        
        return {
            'strengths': strengths,
            'weaknesses': weaknesses,
            'latest_scores': course_performance.to_dict()
        }
