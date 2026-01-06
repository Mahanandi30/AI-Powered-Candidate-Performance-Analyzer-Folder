from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='student') # admin, faculty, student, guest

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    performance_category = db.Column(db.String(20))  # Poor/Medium/High
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    
class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    course_id = db.Column(db.String(50)) 
    course_name = db.Column(db.String(200))
    mark = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(2))
    attempt_number = db.Column(db.Integer, default=1)
    attempt_date = db.Column(db.DateTime, default=datetime.utcnow)
    
class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    course_list = db.Column(db.Text)  # JSON string of courses
    priority_level = db.Column(db.String(10)) 
    assigned_mentor = db.Column(db.Integer, db.ForeignKey('student.id'))
    completion_status = db.Column(db.Float, default=0.0) 
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

class MentorPairing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    mentee_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    course_name = db.Column(db.String(200), nullable=False)
    pairing_date = db.Column(db.DateTime, default=datetime.utcnow)
