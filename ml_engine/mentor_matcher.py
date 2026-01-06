import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class MentorMatcher:
    def __init__(self):
        pass

    def match_mentors_simple(self, df):
        """
        Existing logic: Pair 'Poor' with 'High' in same course.
        """
        pairings = []
        courses = df['course_name'].unique()
        
        for course in courses:
            course_df = df[df['course_name'] == course]
            mentors = course_df[course_df['performance'] == 'High'].to_dict('records')
            mentees = course_df[course_df['performance'] == 'Poor'].to_dict('records')
            
            min_len = min(len(mentors), len(mentees))
            
            for i in range(min_len):
                pairing = {
                    'course': course,
                    'mentor_name': mentors[i]['name'],
                    'mentor_email': mentors[i].get('email', 'N/A'),
                    'mentee_name': mentees[i]['name'],
                    'mentee_email': mentees[i].get('email', 'N/A')
                }
                pairings.append(pairing)
                
            # Handle unmatched mentees
            if len(mentees) > len(mentors):
                for i in range(len(mentors), len(mentees)):
                     pairings.append({
                        'course': course,
                        'mentor_name': 'Unassigned (Waitlist)',
                        'mentor_email': 'N/A',
                        'mentee_name': mentees[i]['name'],
                        'mentee_email': mentees[i].get('email', 'N/A')
                    })
        return pd.DataFrame(pairings)
