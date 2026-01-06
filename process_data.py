import pandas as pd
import numpy as np
import os

def load_data(file_path):
    """
    Loads data from a CSV or Excel file.
    """
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith(('.xls', '.xlsx')):
        return pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload CSV or Excel.")

def clean_data(df):
    """
    Cleans the dataframe:
    - Standardizes column names
    - Handles missing values
    - Ensures numeric types for scores
    """
    # Standardize column names (strip whitespace, lowercase)
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    # Check for expected columns based on user's schema
    # candidate_scores.csv structure: student_id, name, email, course_id, course_name, attempt_id, score, etc.
    if 'score' in df.columns:
        # User data uses 'score'
        pass 
    elif 'mark' in df.columns:
        # Fallback for old sample data
        df.rename(columns={'mark': 'score'}, inplace=True)
        
    if 'student_name' in df.columns:
         df.rename(columns={'student_name': 'name'}, inplace=True)
    
    # Ensure Score is numeric
    if 'score' in df.columns:
        df['score'] = pd.to_numeric(df['score'], errors='coerce')
        df['score'].fillna(0, inplace=True) # Treat missing marks as 0
    
    return df

def categorize_performance(score):
    """
    Categorizes performance based on score.
    """
    if score < 60:
        return 'Poor'
    elif score <= 80:
        return 'Medium'
    else:
        return 'High'

def process_student_data(file_path, feedback_file_path=None):
    """
    Main function to process the student data file.
    Merged with feedback if provided.
    """
    # Load Main Score Data
    df = load_data(file_path)
    df = clean_data(df)
    
    # Load Feedback Data if available
    if feedback_file_path and os.path.exists(feedback_file_path):
        feedback_df = load_data(feedback_file_path)
        feedback_df = clean_data(feedback_df)
        
        # Expecting 'student_id' as common key
        if 'student_id' in df.columns and 'student_id' in feedback_df.columns:
            # Merge feedback into main dataframe
            # We use left join to keep all score records even if no feedback
            # Check if feedback_df has 'feedback' column
            if 'feedback' in feedback_df.columns:
                df = pd.merge(df, feedback_df[['student_id', 'feedback']], on='student_id', how='left')
                df['feedback'].fillna("No feedback available.", inplace=True)
    
    # Required columns check
    required_cols = ['student_id', 'name', 'course_name', 'score']
    # Map from user specific columns if needed
    if 'course' in df.columns and 'course_name' not in df.columns:
        df.rename(columns={'course': 'course_name'}, inplace=True)
        
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # --- Multiple Attempt Logic ---
    # Convert attempt_id to numeric if possible to find max, or count rows
    # If attempt_id is separate, we can group by student_id and course_name
    
    # key for grouping
    group_cols = ['student_id', 'name', 'course_name', 'email']
    
    # Calculate aggregation
    # Best score, Average score, Count attempts
    agg_funcs = {'score': ['max', 'mean', 'count']}
    
    # If we have feedback, we take the first one (assuming it's per student)
    if 'feedback' in df.columns:
        agg_funcs['feedback'] = 'first'
    if 'topic_tags' in df.columns:
         agg_funcs['topic_tags'] = 'first' # Take first available tags
    
    # Perform aggregation
    # This reduces multiple attempts to a single summary row per student per course
    summary_df = df.groupby(group_cols).agg(agg_funcs).reset_index()
    
    # Flatten Hierarchical columns
    summary_df.columns = ['_'.join(col).strip() if col[1] else col[0] for col in summary_df.columns.values]
    
    # Rename for clarity
    summary_df.rename(columns={
        'score_max': 'best_score',
        'score_mean': 'average_score',
        'score_count': 'attempts'
    }, inplace=True)
    
    if 'feedback_first' in summary_df.columns:
        summary_df.rename(columns={'feedback_first': 'feedback'}, inplace=True)
    if 'topic_tags_first' in summary_df.columns:
        summary_df.rename(columns={'topic_tags_first': 'topic_tags'}, inplace=True)

    # Determine Performance Category based on Best Score
    summary_df['performance'] = summary_df['best_score'].apply(categorize_performance)
    
    # Save processed data
    output_path = 'processed_student_data.csv'
    summary_df.to_csv(output_path, index=False)
    
    return summary_df

def identify_weak_areas(df):
    """
    Identify courses where students are performing poorly.
    """
    return weak_performers[['Student_ID', 'Candidate_Name', 'Course_Name', 'Mark', 'Total_Attempts']]

def main():
    # Test with sample data
    sample_file = 'sample_dataset.csv'
    
    print(f"Loading data from {sample_file}...")
    try:
        df = load_data(sample_file)
        print("Data loaded successfully.")
        
        df = clean_data(df)
        print("Data cleaned.")
        
        df = calculate_metrics(df)
        print("Metrics calculated.")
        
        print("\n--- Raw Data with Metrics ---")
        print(df.head())
        
        analyzed_df = analyze_attempts(df)
        print("\n--- Best Attempts Analysis ---")
        print(analyzed_df[['Student_ID', 'Course_Name', 'Mark', 'Performance_Category', 'Total_Attempts']].head())
        
        weak_areas = identify_weak_areas(analyzed_df)
        print("\n--- Weak Areas Identified (Needs Recommendation) ---")
        print(weak_areas)
        
        # Save processed data for next phase
        analyzed_df.to_csv('processed_student_data.csv', index=False)
        print("\nProcessed data saved to 'processed_student_data.csv'")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
