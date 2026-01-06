from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    performance_category = db.Column(db.String(20))
    attempts = db.relationship('Attempt', backref='student', lazy=True)

class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey('student.student_id'), nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    mark = db.Column(db.Float, nullable=False)
    grade = db.Column(db.String(5))
    attempt_number = db.Column(db.Integer, default=1)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey('student.student_id'), nullable=False)
    course_name = db.Column(db.String(100))
    recommended_action = db.Column(db.String(200))

class MentorPairing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course = db.Column(db.String(100))
    mentor_name = db.Column(db.String(100))
    mentee_name = db.Column(db.String(100))
    status = db.Column(db.String(20), default='Active')
