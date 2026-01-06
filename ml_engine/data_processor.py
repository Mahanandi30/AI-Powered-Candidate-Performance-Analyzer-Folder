import pandas as pd
import numpy as np
import os

class DataProcessor:
    def __init__(self):
        self.raw_data = None
        self.processed_data = None
    
    def load_data(self, file_path):
        """
        Loads data from CSV or Excel file.
        """
        if file_path.endswith('.csv'):
            self.raw_data = pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            self.raw_data = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format. Please upload CSV or Excel.")
        return self.raw_data

    def clean_data(self, df):
        """
        Cleans the dataframe: standardizes columns, handles missing values.
        Adapted to handle user's specific columns ('score', 'mark').
        """
        # Standardize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Mapping for Score
        if 'mark' in df.columns:
            df.rename(columns={'mark': 'score'}, inplace=True)
        
        # Mapping for Name
        if 'candidate_name' in df.columns:
            df.rename(columns={'candidate_name': 'name'}, inplace=True)
        elif 'student_name' in df.columns:
            df.rename(columns={'student_name': 'name'}, inplace=True)

        # Mapping for Course
        if 'course' in df.columns:
            df.rename(columns={'course': 'course_name'}, inplace=True)
        
        # Mapping for Email
        if 'candidate_email' in df.columns:
            df.rename(columns={'candidate_email': 'email'}, inplace=True)

        # Ensure numeric Score
        if 'score' in df.columns:
            df['score'] = pd.to_numeric(df['score'], errors='coerce')
            df['score'].fillna(0, inplace=True)
            
        return df

    def process_student_data(self, file_path, feedback_file_path=None):
        """
        Main processing logic, including merging feedback and aggregating attempts.
        """
        df = self.load_data(file_path)
        df = self.clean_data(df)
        
        # Load Feedback if available
        if feedback_file_path and os.path.exists(feedback_file_path):
            feedback_df = self.load_data(feedback_file_path)
            feedback_df = self.clean_data(feedback_df)
            
            # Merge on student_id if possible
            if 'student_id' in df.columns and 'student_id' in feedback_df.columns:
                if 'feedback' in feedback_df.columns:
                    df = pd.merge(df, feedback_df[['student_id', 'feedback']], on='student_id', how='left')
                    df['feedback'].fillna("No feedback available.", inplace=True)
        
        # Aggregation Logic (Best Score logic)
        # Attempting to group by Student Identifier (Email preferred, else Name/ID)
        group_cols = []
        possible_ids = ['student_id', 'email', 'name', 'course_name']
        for col in possible_ids:
            if col in df.columns:
                group_cols.append(col)
        
        if not group_cols:
             raise ValueError("Data lacks necessary identification columns (student_id, email, or name).")

        # Ensure sorting for 'latest' logic
        if 'attempt_timestamp' in df.columns:
            df['attempt_timestamp'] = pd.to_datetime(df['attempt_timestamp'], errors='coerce')
            df.sort_values(by=['email', 'course_name', 'attempt_timestamp'], inplace=True)

        agg_funcs = {'score': ['max', 'mean', 'count', 'std', 'last']}
        
        if 'feedback' in df.columns:
            agg_funcs['feedback'] = 'first'
        if 'topic_tags' in df.columns:
            agg_funcs['topic_tags'] = 'first'
            
        summary_df = df.groupby(group_cols).agg(agg_funcs).reset_index()
        
        # Flatten columns
        summary_df.columns = ['_'.join(col).strip() if col[1] else col[0] for col in summary_df.columns.values]
        
        # Renaissance
        rename_map = {
            'score_max': 'best_score',
            'score_mean': 'average_score',
            'score_count': 'attempts',
            'score_std': 'std_score',
            'score_last': 'latest_score',
            'feedback_first': 'feedback',
            'topic_tags_first': 'topic_tags'
        }
        summary_df.rename(columns=rename_map, inplace=True)
        
        # Fill NaN std (single attempts) with 0
        if 'std_score' in summary_df.columns:
            summary_df['std_score'].fillna(0, inplace=True)
        
        # Save detailed data for progress tracking
        df.to_csv('detailed_student_analysis.csv', index=False)

        self.processed_data = summary_df
        return summary_df
