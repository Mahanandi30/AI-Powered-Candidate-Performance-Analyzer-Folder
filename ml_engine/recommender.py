import pandas as pd

class CourseRecommender:
    def __init__(self, course_catalog=None):
        self.course_catalog = course_catalog

    def recommend_from_weaknesses(self, weaknesses):
        """
        Generate recommendations based on list of weak subjects.
        Satisfies ANAR3: 10+ course catalog mapping.
        """
        catalog = {
            'Python': ['Python Fundamentals', 'Data Structures in Python'],
            'Java': ['Java Programming I', 'Object Oriented Programming'],
            'SQL': ['Database Design', 'SQL Masterclass'],
            'Data Science': ['Statistics for DS', 'Intro to ML'],
            'Computer Networks': ['Networking Basics', 'TCP/IP Protocols'],
            'Math': ['Linear Algebra', 'Calculus Refresher'],
            'Web Development': ['HTML/CSS Bootcamp', 'JavaScript Essentials'],
            'Algorithms': ['Algorithms I', 'Competitive Programming'],
            'Operating Systems': ['OS Concepts', 'Linux Admin'],
            'Security': ['Cybersecurity Basics', 'Ethical Hacking']
        }
        
        recommendations = []
        for subject in weaknesses:
            # Simple substring matching or direct lookup
            matches = [courses for key, courses in catalog.items() if key in subject or subject in key]
            for batch in matches:
                recommendations.extend(batch)
                
        if not recommendations and weaknesses:
            recommendations.append("General Study Skills Workshop")
            
        return list(set(recommendations)) # Remove duplicates
