import pandas as pd
import numpy as np

def load_processed_data(filepath='processed_student_data.csv'):
    """
    Load the processed student data.
    """
    try:
        return pd.read_csv(filepath)
    except FileNotFoundError:
        print("Processed data file not found. Please run process_data.py first.")
        return None

def recommend_courses(row):
    """
    Simple rule-based recommender.
    If performance is Poor, recommend remedial course.
    """
    if row['performance'] == 'Poor':
        return f"Remedial: {row['course_name']} Refresher"
    elif row['performance'] == 'Medium':
        return f"Advanced: {row['course_name']} Plus"
    else:
        return "Mentorship Program (Become a Mentor)"

def match_mentors(df):
    """
    Pair 'Poor' performers with 'High' performers in the same course.
    """
    pairings = []
    
    # Group by Course
    courses = df['course_name'].unique()
    
    for course in courses:
        course_df = df[df['course_name'] == course]
        
        # Separate potential mentors and mentees
        mentors = course_df[course_df['performance'] == 'High']
        mentees = course_df[course_df['performance'] == 'Poor']
        
        # Simple pairing logic: First available mentor for each mentee
        mentors_list = mentors.to_dict('records')
        mentees_list = mentees.to_dict('records')
        
        min_len = min(len(mentors_list), len(mentees_list))
        
        for i in range(min_len):
            pairing = {
                'course': course,
                'mentor_name': mentors_list[i]['name'],
                'mentor_email': mentors_list[i].get('email', 'N/A'),
                'mentee_name': mentees_list[i]['name'],
                'mentee_email': mentees_list[i].get('email', 'N/A')
            }
            pairings.append(pairing)
            
        # Handle unmatched
        if len(mentees_list) > len(mentors_list):
            for i in range(len(mentors_list), len(mentees_list)):
                 pairings.append({
                    'course': course,
                    'mentor_name': 'Unassigned (Waitlist)',
                    'mentor_email': 'N/A',
                    'mentee_name': mentees_list[i]['name'],
                    'mentee_email': mentees_list[i].get('email', 'N/A')
                })
                
    return pd.DataFrame(pairings)

def main():
    print("Loading processed data...")
    df = load_processed_data()
    
    if df is not None:
        # 1. Generate Recommendations
        print("Generating Course Recommendations...")
        df['recommended_action'] = df.apply(recommend_courses, axis=1)
        
        print("\n--- Student Recommendations Sample ---")
        print(df[['name', 'course_name', 'performance', 'recommended_action']].head())
        
        # 2. Mentor Matching
        print("\nRunning Mentor Matching Algorithm...")
        pairings_df = match_mentors(df)
        
        if not pairings_df.empty:
            print("\n--- Mentor-Mentee Pairings ---")
            print(pairings_df.head())
            pairings_df.to_csv('mentor_pairings.csv', index=False)
            print("Pairings saved to 'mentor_pairings.csv'")
        else:
            print("No pairings could be formed (lack of matches).")
            
        # Save updated main data with recommendations
        df.to_csv('final_student_analysis.csv', index=False)
        print("Final analysis saved to 'final_student_analysis.csv'")

if __name__ == "__main__":
    main()

