"""
Main Flask application for AI-Powered Candidate Performance Analyzer
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, make_response
import pandas as pd
import numpy as np
import os
import sqlite3
from datetime import datetime
import json
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from sklearn.cluster import KMeans
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LinearRegression
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

app = Flask(__name__)

# Database configuration
DATABASE = 'performance_analyzer.db'

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables"""
    conn = get_db_connection()
    
    # Create students table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create courses table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT UNIQUE NOT NULL,
            course_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create scores table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_id TEXT NOT NULL,
            attempt_id INTEGER,
            attempt_timestamp TIMESTAMP,
            score REAL,
            max_score REAL,
            grade TEXT,
            topic_tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (student_id),
            FOREIGN KEY (course_id) REFERENCES courses (course_id)
        )
    ''')
    
    # Create recommendations table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_id TEXT NOT NULL,
            recommendation TEXT,
            priority TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (student_id),
            FOREIGN KEY (course_id) REFERENCES courses (course_id)
        )
    ''')
    
    # Create pairings table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS pairings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT NOT NULL,
            weak_student_id TEXT NOT NULL,
            mentor_id TEXT NOT NULL,
            compatibility_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses (course_id),
            FOREIGN KEY (weak_student_id) REFERENCES students (student_id),
            FOREIGN KEY (mentor_id) REFERENCES students (student_id)
        )
    ''')
    
    # Create course completions table for tracking progress
    conn.execute('''
        CREATE TABLE IF NOT EXISTS course_completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_id TEXT NOT NULL,
            completion_date TIMESTAMP,
            completion_status TEXT DEFAULT 'in_progress',  -- in_progress, completed, abandoned
            completion_percentage REAL DEFAULT 0,
            estimated_completion_time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (student_id),
            FOREIGN KEY (course_id) REFERENCES courses (course_id)
        )
    ''')
    
    # Create improvement tracking table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS improvement_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_id TEXT NOT NULL,
            initial_score REAL,
            final_score REAL,
            improvement_percentage REAL,
            completion_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (student_id),
            FOREIGN KEY (course_id) REFERENCES courses (course_id)
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard page with overall class performance"""
    conn = get_db_connection()
    
    # Get total number of students
    total_students = conn.execute('SELECT COUNT(*) as count FROM students').fetchone()['count']
    
    # Get total number of courses
    total_courses = conn.execute('SELECT COUNT(*) as count FROM courses').fetchone()['count']
    
    # Get performance distribution
    performance_data = conn.execute('''
        SELECT s.performance, COUNT(*) as count 
        FROM (
            SELECT student_id, 
                CASE 
                    WHEN avg_score >= 75 THEN 'High'
                    WHEN avg_score >= 60 THEN 'Medium'
                    ELSE 'Low'
                END as performance
            FROM (
                SELECT student_id, AVG(score) as avg_score
                FROM scores
                GROUP BY student_id
            ) as student_avg
        ) as s
        GROUP BY s.performance
    ''').fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         total_students=total_students, 
                         total_courses=total_courses,
                         performance_data=performance_data)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Data upload page"""
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'})
        
        if file and file.filename.endswith(('.csv', '.xlsx', '.xls')):
            try:
                # Save file temporarily
                filepath = os.path.join('uploads', file.filename)
                os.makedirs('uploads', exist_ok=True)
                file.save(filepath)
                
                # Process the file based on extension
                if file.filename.endswith('.csv'):
                    df = pd.read_csv(filepath)
                else:  # Excel files
                    df = pd.read_excel(filepath)
                
                # Validate required columns
                required_columns = ['student_id', 'name', 'email', 'course_id', 'course_name', 
                                  'attempt_id', 'attempt_timestamp', 'score', 'max_score', 'grade']
                
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    return jsonify({'error': f'Missing required columns: {missing_columns}'})
                
                # Process and store data
                process_uploaded_data(df)
                
                # Generate initial analytics after upload
                generate_initial_analytics(df)
                
                return jsonify({'success': True, 'message': 'Data uploaded and processed successfully'})
            except Exception as e:
                return jsonify({'error': f'Error processing file: {str(e)}'})
        else:
            return jsonify({'error': 'Invalid file format. Please upload CSV or Excel file.'})
    
    return render_template('upload.html')

def process_uploaded_data(df):
    """Process and store uploaded data in database"""
    conn = get_db_connection()
    
    # Insert unique students
    students_df = df[['student_id', 'name', 'email']].drop_duplicates()
    for _, row in students_df.iterrows():
        try:
            conn.execute(
                'INSERT OR IGNORE INTO students (student_id, name, email) VALUES (?, ?, ?)',
                (row['student_id'], row['name'], row['email'])
            )
        except sqlite3.Error:
            pass
    
    # Insert unique courses
    courses_df = df[['course_id', 'course_name']].drop_duplicates()
    for _, row in courses_df.iterrows():
        try:
            conn.execute(
                'INSERT OR IGNORE INTO courses (course_id, course_name) VALUES (?, ?)',
                (row['course_id'], row['course_name'])
            )
        except sqlite3.Error:
            pass
    
    # Insert scores
    for _, row in df.iterrows():
        try:
            conn.execute('''
                INSERT INTO scores 
                (student_id, course_id, attempt_id, attempt_timestamp, score, max_score, grade, topic_tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['student_id'], 
                row['course_id'], 
                row['attempt_id'], 
                row['attempt_timestamp'], 
                row['score'], 
                row['max_score'], 
                row['grade'], 
                row.get('topic_tags', '')
            ))
        except sqlite3.Error:
            pass
    
    conn.commit()
    conn.close()


def generate_initial_analytics(df):
    """Generate initial analytics and recommendations after data upload"""
    conn = get_db_connection()
    
    # Calculate performance metrics and classify students
    for student_id in df['student_id'].unique():
        student_data = df[df['student_id'] == student_id]
        
        # Calculate average score per course for this student
        avg_scores = student_data.groupby('course_id')['score'].mean()
        
        for course_id, avg_score in avg_scores.items():
            # Classify performance
            if avg_score >= 75:
                performance_level = 'High'
            elif avg_score >= 60:
                performance_level = 'Medium'
            else:
                performance_level = 'Low'
            
            # Identify weak topics for recommendations
            if performance_level == 'Low':
                # Get topic tags for this course
                course_data = student_data[student_data['course_id'] == course_id]
                if not course_data.empty:
                    topic_tags = course_data.iloc[0]['topic_tags']
                    
                    # Insert recommendation
                    try:
                        conn.execute('''
                            INSERT OR IGNORE INTO recommendations 
                            (student_id, course_id, recommendation, priority)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            student_id,
                            course_id,
                            f'Review topics: {topic_tags}',
                            'High'
                        ))
                    except sqlite3.Error:
                        pass
                    
                    # Track this as a course that needs improvement
                    track_course_completion(student_id, course_id, completion_percentage=0, status='recommended')
    
    # Generate mentor pairings
    generate_mentor_pairings(conn)
    
    conn.commit()
    conn.close()


def generate_course_recommendations(student_id):
    """Generate personalized course recommendations for a student"""
    conn = get_db_connection()
    
    # Get student's weak areas
    student_analysis = get_student_strengths_weaknesses(student_id)
    
    recommendations = []
    
    # For each weak area, suggest related courses or resources
    for weakness in student_analysis['weaknesses']:
        course_id = weakness['course_id']
        course_name = weakness['course_name']
        
        # Find similar courses that might help
        similar_courses = conn.execute('''
            SELECT course_id, course_name, avg_score
            FROM (
                SELECT 
                    s2.course_id,
                    c.course_name,
                    AVG(s2.score) as avg_score,
                    COUNT(s2.student_id) as student_count
                FROM scores s1
                JOIN scores s2 ON s1.student_id = s2.student_id
                JOIN courses c ON s2.course_id = c.course_id
                WHERE s1.course_id = ? AND s1.score < 60
                GROUP BY s2.course_id, c.course_name
                HAVING student_count > 1
            ) as similar
            ORDER BY avg_score DESC
            LIMIT 3
        ''', (course_id,)).fetchall()
        
        # Add recommendation
        recommendations.append({
            'course_id': course_id,
            'course_name': course_name,
            'current_performance': weakness['percentage'],
            'recommended_courses': [dict(course) for course in similar_courses],
            'priority': 'High',
            'recommendation_text': f'Study foundational topics in {course_name} to improve performance'
        })
    
    # Also suggest courses that complement weak areas
    for weakness in student_analysis['weaknesses']:
        course_name = weakness['course_name']
        
        # Look for courses that are prerequisites or complementary
        if 'Machine Learning' in course_name:
            # Suggest math/statistics courses
            math_courses = conn.execute('''
                SELECT course_id, course_name, AVG(score) as avg_score
                FROM scores s
                JOIN courses c ON s.course_id = c.course_id
                WHERE c.course_name LIKE '%Math%' OR c.course_name LIKE '%Statistics%' OR c.course_name LIKE '%Data%'
                GROUP BY s.course_id, c.course_name
                ORDER BY avg_score DESC
                LIMIT 2
            ''').fetchall()
            
            for course in math_courses:
                recommendations.append({
                    'course_id': course['course_id'],
                    'course_name': course['course_name'],
                    'current_performance': weakness['percentage'],
                    'recommended_courses': [],
                    'priority': 'Medium',
                    'recommendation_text': f'Build foundational math skills to support {course_name} learning'
                })
    
    conn.close()
    return recommendations


def get_recommendations_for_student(student_id):
    """Get recommendations for a specific student"""
    conn = get_db_connection()
    
    # Get stored recommendations
    recs = conn.execute('''
        SELECT r.course_id, c.course_name, r.recommendation, r.priority
        FROM recommendations r
        JOIN courses c ON r.course_id = c.course_id
        WHERE r.student_id = ?
        ORDER BY 
            CASE r.priority
                WHEN 'High' THEN 1
                WHEN 'Medium' THEN 2
                WHEN 'Low' THEN 3
            END
    ''', (student_id,)).fetchall()
    
    conn.close()
    
    return [dict(rec) for rec in recs]


def update_recommendations():
    """Update recommendations for all students based on latest performance"""
    conn = get_db_connection()
    
    # Get all students
    students = conn.execute('SELECT student_id FROM students').fetchall()
    
    for student in students:
        student_id = student['student_id']
        
        # Clear old recommendations for this student
        conn.execute('DELETE FROM recommendations WHERE student_id = ?', (student_id,))
        
        # Generate new recommendations
        new_recs = generate_course_recommendations(student_id)
        
        # Insert new recommendations
        for rec in new_recs:
            try:
                conn.execute('''
                    INSERT INTO recommendations
                    (student_id, course_id, recommendation, priority)
                    VALUES (?, ?, ?, ?)
                ''', (
                    student_id,
                    rec['course_id'],
                    rec['recommendation_text'],
                    rec['priority']
                ))
            except sqlite3.Error:
                pass
    
    conn.commit()
    conn.close()


def generate_mentor_pairings(conn):
    """Generate mentor pairings based on performance levels"""
    # Get all students with their average scores and course performance
    student_performance = conn.execute('''
        SELECT 
            s.student_id,
            s.name,
            AVG(sc.score) as avg_score,
            COUNT(sc.course_id) as total_courses
        FROM students s
        JOIN scores sc ON s.student_id = sc.student_id
        GROUP BY s.student_id, s.name
    ''').fetchall()
    
    # Categorize students
    strong_students = []
    weak_students = []
    
    for student in student_performance:
        student_id = student['student_id']
        avg_score = student['avg_score']
        
        # More nuanced classification
        if avg_score >= 75:
            strong_students.append({
                'student_id': student_id,
                'avg_score': avg_score,
                'name': student['name']
            })
        elif avg_score < 60:
            weak_students.append({
                'student_id': student_id,
                'avg_score': avg_score,
                'name': student['name']
            })
    
    # Sort strong students by average score (descending) for best mentors
    strong_students.sort(key=lambda x: x['avg_score'], reverse=True)
    
    # Create pairings based on course-specific performance
    for weak_student in weak_students:
        weak_student_id = weak_student['student_id']
        
        # Get specific courses where weak student is struggling
        weak_courses = conn.execute('''
            SELECT 
                sc.course_id,
                c.course_name,
                AVG(sc.score) as avg_score,
                MAX(sc.score) as max_score,
                sc.max_score as total_possible
            FROM scores sc
            JOIN courses c ON sc.course_id = c.course_id
            WHERE sc.student_id = ?
            GROUP BY sc.course_id, c.course_name, sc.max_score
            HAVING avg_score < 60
            ORDER BY avg_score ASC  -- Most problematic courses first
        ''', (weak_student_id,)).fetchall()
        
        for course in weak_courses:
            course_id = course['course_id']
            course_name = course['course_name']
            
            # Find strong students who excel in this specific course
            potential_mentors = conn.execute('''
                SELECT 
                    s.student_id,
                    s.name,
                    AVG(sc.score) as avg_score,
                    MAX(sc.score) as max_score
                FROM students s
                JOIN scores sc ON s.student_id = sc.student_id
                WHERE sc.course_id = ?
                GROUP BY s.student_id, s.name
                HAVING avg_score >= 75
                ORDER BY avg_score DESC
                LIMIT 5  -- Top 5 performers in this course
            ''', (course_id,)).fetchall()
            
            # Pair weak student with top mentors for this course
            for i, mentor in enumerate(potential_mentors):
                if i >= 2:  # Limit to 2 mentors per course per student
                    break
                
                mentor_id = mentor['student_id']
                
                # Calculate compatibility score based on course performance
                mentor_avg = mentor['avg_score']
                weak_avg = course['avg_score']
                
                # Compatibility score calculation
                # Higher score if mentor significantly outperforms the weak student
                score_diff = mentor_avg - weak_avg
                compatibility_score = min(100, max(50, 70 + (score_diff * 0.5)))
                
                try:
                    conn.execute('''
                        INSERT OR IGNORE INTO pairings
                        (course_id, weak_student_id, mentor_id, compatibility_score)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        course_id,
                        weak_student_id,
                        mentor_id,
                        compatibility_score
                    ))
                except sqlite3.Error:
                    pass


def get_mentor_pairings_for_student(student_id):
    """Get mentor pairings for a specific weak student"""
    conn = get_db_connection()
    
    pairings = conn.execute('''
        SELECT 
            p.course_id,
            c.course_name,
            s.name as mentor_name,
            p.compatibility_score
        FROM pairings p
        JOIN students s ON p.mentor_id = s.student_id
        JOIN courses c ON p.course_id = c.course_id
        WHERE p.weak_student_id = ?
        ORDER BY p.compatibility_score DESC
    ''', (student_id,)).fetchall()
    
    conn.close()
    
    return [dict(pairing) for pairing in pairings]


def get_mentee_list_for_mentor(mentor_id):
    """Get list of students mentored by a specific mentor"""
    conn = get_db_connection()
    
    mentees = conn.execute('''
        SELECT 
            p.course_id,
            c.course_name,
            s.name as weak_student_name,
            p.compatibility_score
        FROM pairings p
        JOIN students s ON p.weak_student_id = s.student_id
        JOIN courses c ON p.course_id = c.course_id
        WHERE p.mentor_id = ?
        ORDER BY p.compatibility_score DESC
    ''', (mentor_id,)).fetchall()
    
    conn.close()
    
    return [dict(mentee) for mentee in mentees]

@app.route('/students')
def students():
    """Students analysis page"""
    conn = get_db_connection()
    
    # Get all students with their average scores
    students_data = conn.execute('''
        SELECT s.student_id, s.name, s.email, AVG(sc.score) as avg_score
        FROM students s
        LEFT JOIN scores sc ON s.student_id = sc.student_id
        GROUP BY s.student_id, s.name, s.email
        ORDER BY avg_score DESC
    ''').fetchall()
    
    conn.close()
    
    return render_template('students.html', students=students_data)

@app.route('/recommendations')
def recommendations():
    """Course recommendations page"""
    conn = get_db_connection()
    
    # Get recommendations with student and course info
    recommendations_data = conn.execute('''
        SELECT r.student_id, s.name, c.course_name, r.recommendation, r.priority
        FROM recommendations r
        JOIN students s ON r.student_id = s.student_id
        JOIN courses c ON r.course_id = c.course_id
    ''').fetchall()
    
    conn.close()
    
    return render_template('recommendations.html', recommendations=recommendations_data)

@app.route('/pairings')
def pairings():
    """Mentor pairing page"""
    conn = get_db_connection()
    
    # Get pairings with student names
    pairings_data = conn.execute('''
        SELECT p.course_id, c.course_name, 
               ws.name as weak_student_name, ms.name as mentor_name, 
               p.compatibility_score
        FROM pairings p
        JOIN students ws ON p.weak_student_id = ws.student_id
        JOIN students ms ON p.mentor_id = ms.student_id
        JOIN courses c ON p.course_id = c.course_id
    ''').fetchall()
    
    conn.close()
    
    return render_template('pairings.html', pairings=pairings_data)

@app.route('/reports')
def reports():
    """Reports page"""
    conn = get_db_connection()
    
    # Get all students
    students = conn.execute('''
        SELECT student_id, name, email 
        FROM students 
        ORDER BY name
    ''').fetchall()
    
    conn.close()
    
    return render_template('reports.html', students=students)


@app.route('/progress')
def progress():
    """Student progress tracking page"""
    conn = get_db_connection()
    
    # Get all students
    students = conn.execute('''
        SELECT student_id, name, email 
        FROM students 
        ORDER BY name
    ''').fetchall()
    
    conn.close()
    
    return render_template('student_progress.html', students=students)

@app.route('/api/student/<student_id>')
def get_student_data(student_id):
    """API endpoint to get student data"""
    conn = get_db_connection()
    
    # Get student info
    student = conn.execute(
        'SELECT * FROM students WHERE student_id = ?', (student_id,)
    ).fetchone()
    
    # Get student scores
    scores = conn.execute('''
        SELECT c.course_name, sc.score, sc.max_score, sc.grade, sc.attempt_timestamp
        FROM scores sc
        JOIN courses c ON sc.course_id = c.course_id
        WHERE sc.student_id = ?
        ORDER BY sc.attempt_timestamp DESC
    ''', (student_id,)).fetchall()
    
    conn.close()
    
    if student:
        return jsonify({
            'student': dict(student),
            'scores': [dict(score) for score in scores]
        })
    else:
        return jsonify({'error': 'Student not found'}), 404

@app.route('/api/analytics')
def get_analytics():
    """API endpoint to get analytics data"""
    conn = get_db_connection()
    
    # Get overall statistics
    total_students = conn.execute('SELECT COUNT(*) as count FROM students').fetchone()['count']
    total_courses = conn.execute('SELECT COUNT(*) as count FROM courses').fetchone()['count']
    total_scores = conn.execute('SELECT COUNT(*) as count FROM scores').fetchone()['count']
    
    # Get performance distribution
    performance_dist = conn.execute('''
        SELECT 
            CASE 
                WHEN avg_score >= 75 THEN 'High'
                WHEN avg_score >= 60 THEN 'Medium'
                ELSE 'Low'
            END as performance_level,
            COUNT(*) as count
        FROM (
            SELECT student_id, AVG(score) as avg_score
            FROM scores
            GROUP BY student_id
        ) as student_avg
        GROUP BY performance_level
    ''').fetchall()
    
    # Get top performers
    top_performers = conn.execute('''
        SELECT s.name, AVG(sc.score) as avg_score
        FROM students s
        JOIN scores sc ON s.student_id = sc.student_id
        GROUP BY s.student_id, s.name
        ORDER BY avg_score DESC
        LIMIT 5
    ''').fetchall()
    
    # Get course-wise performance
    course_performance = conn.execute('''
        SELECT c.course_name, AVG(sc.score) as avg_score, COUNT(sc.student_id) as student_count
        FROM courses c
        JOIN scores sc ON c.course_id = sc.course_id
        GROUP BY c.course_id, c.course_name
        ORDER BY avg_score DESC
    ''').fetchall()
    
    conn.close()
    
    return jsonify({
        'total_students': total_students,
        'total_courses': total_courses,
        'total_scores': total_scores,
        'performance_distribution': [dict(row) for row in performance_dist],
        'top_performers': [dict(row) for row in top_performers],
        'course_performance': [dict(row) for row in course_performance]
    })


@app.route('/api/progress/<student_id>')
def get_student_progress(student_id):
    """API endpoint to get student progress and improvement data"""
    # Get student improvement data
    improvement_data = calculate_overall_improvement(student_id)
    
    # Get specific improvement tracking
    improvements = get_improvement_tracking(student_id)
    
    # Get course completion status
    conn = get_db_connection()
    completion_status = conn.execute('''
        SELECT 
            c.course_name,
            cc.completion_status,
            cc.completion_percentage,
            cc.estimated_completion_time
        FROM course_completions cc
        JOIN courses c ON cc.course_id = c.course_id
        WHERE cc.student_id = ?
        ORDER BY cc.created_at DESC
    ''', (student_id,)).fetchall()
    conn.close()
    
    return jsonify({
        'improvement_data': improvement_data,
        'improvements': improvements,
        'completion_status': [dict(status) for status in completion_status]
    })


@app.route('/api/improvement/most-improved')
def get_most_improved():
    """API endpoint to get most improved students"""
    most_improved = get_most_improved_students(limit=5)
    
    return jsonify({'most_improved_students': most_improved})


@app.route('/api/progress/track', methods=['POST'])
def track_progress():
    """API endpoint to track course completion"""
    data = request.json
    student_id = data.get('student_id')
    course_id = data.get('course_id')
    completion_percentage = data.get('completion_percentage', 0)
    status = data.get('status', 'in_progress')
    estimated_time = data.get('estimated_time')
    
    if not student_id or not course_id:
        return jsonify({'error': 'student_id and course_id are required'}), 400
    
    track_course_completion(student_id, course_id, completion_percentage, status, estimated_time)
    
    return jsonify({'success': True, 'message': 'Progress tracked successfully'})


@app.route('/api/progress/complete', methods=['POST'])
def mark_completion():
    """API endpoint to mark course as completed"""
    data = request.json
    student_id = data.get('student_id')
    course_id = data.get('course_id')
    
    if not student_id or not course_id:
        return jsonify({'error': 'student_id and course_id are required'}), 400
    
    mark_course_completed(student_id, course_id)
    
    return jsonify({'success': True, 'message': 'Course marked as completed'})


@app.route('/api/progress/update', methods=['POST'])
def update_progress():
    """API endpoint to update course progress"""
    data = request.json
    student_id = data.get('student_id')
    course_id = data.get('course_id')
    completion_percentage = data.get('completion_percentage', 0)
    status = data.get('status', 'in_progress')
    estimated_time = data.get('estimated_time')
    
    if not student_id or not course_id:
        return jsonify({'error': 'student_id and course_id are required'}), 400
    
    track_course_completion(student_id, course_id, completion_percentage, status, estimated_time)
    
    return jsonify({'success': True, 'message': 'Progress updated successfully'})


@app.route('/api/pairings')
def get_pairings_data():
    """API endpoint to get pairings data for reports"""
    conn = get_db_connection()
    
    # Get all pairings with student names
    pairings_data = conn.execute('''
        SELECT p.course_id, c.course_name, 
               ws.name as weak_student_name, ms.name as mentor_name, 
               p.compatibility_score
        FROM pairings p
        JOIN students ws ON p.weak_student_id = ws.student_id
        JOIN students ms ON p.mentor_id = ms.student_id
        JOIN courses c ON p.course_id = c.course_id
    ''').fetchall()
    
    conn.close()
    
    return jsonify({'pairings': [dict(pairing) for pairing in pairings_data]})


@app.route('/api/recommendations')
def get_recommendations_data():
    """API endpoint to get recommendations data for reports"""
    conn = get_db_connection()
    
    # Get all recommendations with student and course names
    recommendations_data = conn.execute('''
        SELECT r.student_id, s.name as student_name, c.course_name, r.recommendation, r.priority
        FROM recommendations r
        JOIN students s ON r.student_id = s.student_id
        JOIN courses c ON r.course_id = c.course_id
    ''').fetchall()
    
    conn.close()
    
    return jsonify({'recommendations': [dict(rec) for rec in recommendations_data]})


@app.route('/api/ml/performance-classification')
def get_ml_performance_classification():
    """API endpoint to get ML-based performance classification"""
    classification = ml_performance_classification()
    return jsonify({'classification': classification})


@app.route('/api/ml/improvement-prediction/<student_id>')
def get_ml_improvement_prediction(student_id):
    """API endpoint to get ML-based improvement prediction for a student"""
    prediction = ml_improvement_prediction(student_id)
    return jsonify(prediction)


@app.route('/api/ml/recommendations/<student_id>')
def get_ml_recommendations(student_id):
    """API endpoint to get ML-based course recommendations for a student"""
    recommendations = ml_course_recommendation_ml(student_id)
    return jsonify({'recommendations': recommendations})


@app.route('/api/ml/mentors/<student_id>')
def get_ml_mentor_matches(student_id):
    """API endpoint to get ML-based mentor matches for a student"""
    # Using cosine similarity for mentor matching
    matches = ml_mentor_matching_ml(student_id)
    return jsonify({'matches': matches})


def analyze_student_performance(student_id):
    """Analyze a specific student's performance to identify strengths and weaknesses"""
    conn = get_db_connection()
    
    # Get all scores for the student
    scores = conn.execute('''
        SELECT c.course_name, s.score, s.max_score, s.grade, s.attempt_timestamp
        FROM scores s
        JOIN courses c ON s.course_id = c.course_id
        WHERE s.student_id = ?
        ORDER BY s.attempt_timestamp
    ''', (student_id,)).fetchall()
    
    # Calculate performance metrics
    performance_analysis = {
        'student_id': student_id,
        'strengths': [],  # Courses where score >= 75
        'weaknesses': [],  # Courses where score < 60
        'improvement_areas': [],  # Courses showing declining performance
        'overall_performance': 0,
        'performance_trend': 'stable'  # increasing, decreasing, stable
    }
    
    if scores:
        total_score = 0
        total_courses = 0
        
        # Group scores by course to analyze each course separately
        course_scores = {}
        for score in scores:
            course_name = score['course_name']
            if course_name not in course_scores:
                course_scores[course_name] = []
            course_scores[course_name].append(score)
        
        # Analyze each course
        for course_name, course_data in course_scores.items():
            latest_score = course_data[-1]['score']  # Last attempt
            avg_score = sum(s['score'] for s in course_data) / len(course_data)
            max_score = course_data[0]['max_score']  # Assuming max_score is consistent per course
            
            # Calculate percentage
            percentage = (latest_score / max_score) * 100 if max_score > 0 else 0
            
            # Classify performance
            if percentage >= 75:
                performance_analysis['strengths'].append({
                    'course': course_name,
                    'score': latest_score,
                    'percentage': percentage
                })
            elif percentage < 60:
                performance_analysis['weaknesses'].append({
                    'course': course_name,
                    'score': latest_score,
                    'percentage': percentage
                })
            
            # Check for improvement trend
            if len(course_data) > 1:
                first_score = course_data[0]['score']
                last_score = course_data[-1]['score']
                improvement = last_score - first_score
                
                if improvement < -10:  # Dropped significantly
                    performance_analysis['improvement_areas'].append({
                        'course': course_name,
                        'first_score': first_score,
                        'last_score': last_score,
                        'improvement': improvement
                    })
            
            total_score += avg_score
            total_courses += 1
        
        if total_courses > 0:
            performance_analysis['overall_performance'] = total_score / total_courses
        
        # Determine overall trend
        if scores:
            first_overall = scores[0]['score']
            last_overall = scores[-1]['score']
            overall_change = last_overall - first_overall
            
            if overall_change > 10:
                performance_analysis['performance_trend'] = 'increasing'
            elif overall_change < -10:
                performance_analysis['performance_trend'] = 'decreasing'
            
    conn.close()
    return performance_analysis


def get_class_performance_analysis():
    """Analyze overall class performance"""
    conn = get_db_connection()
    
    # Get overall class metrics
    class_metrics = conn.execute('''
        SELECT 
            AVG(score) as avg_class_score,
            MIN(score) as min_class_score,
            MAX(score) as max_class_score,
            COUNT(DISTINCT student_id) as total_students,
            COUNT(DISTINCT course_id) as total_courses
        FROM scores
    ''').fetchone()
    
    # Get performance distribution
    performance_dist = conn.execute('''
        SELECT 
            CASE 
                WHEN avg_score >= 75 THEN 'High'
                WHEN avg_score >= 60 THEN 'Medium'
                ELSE 'Low'
            END as performance_level,
            COUNT(*) as count
        FROM (
            SELECT student_id, AVG(score) as avg_score
            FROM scores
            GROUP BY student_id
        ) as student_avg
        GROUP BY performance_level
    ''').fetchall()
    
    # Get subject-wise performance
    subject_performance = conn.execute('''
        SELECT 
            c.course_name,
            AVG(s.score) as avg_score,
            MIN(s.score) as min_score,
            MAX(s.score) as max_score,
            COUNT(s.student_id) as student_count
        FROM scores s
        JOIN courses c ON s.course_id = c.course_id
        GROUP BY c.course_id, c.course_name
        ORDER BY avg_score DESC
    ''').fetchall()
    
    conn.close()
    
    return {
        'class_metrics': dict(class_metrics) if class_metrics else {},
        'performance_distribution': [dict(row) for row in performance_dist],
        'subject_performance': [dict(row) for row in subject_performance]
    }


def get_student_strengths_weaknesses(student_id):
    """Get specific strengths and weaknesses for a student"""
    conn = get_db_connection()
    
    # Get all scores for the student
    student_scores = conn.execute('''
        SELECT 
            s.course_id,
            c.course_name,
            AVG(s.score) as avg_score,
            MAX(s.score) as max_score,
            s.max_score as total_possible
        FROM scores s
        JOIN courses c ON s.course_id = c.course_id
        WHERE s.student_id = ?
        GROUP BY s.course_id, c.course_name, s.max_score
    ''', (student_id,)).fetchall()
    
    strengths = []
    weaknesses = []
    
    for score in student_scores:
        if score['total_possible'] > 0:
            percentage = (score['avg_score'] / score['total_possible']) * 100
            
            if percentage >= 75:
                strengths.append({
                    'course_id': score['course_id'],
                    'course_name': score['course_name'],
                    'avg_score': round(score['avg_score'], 2),
                    'percentage': round(percentage, 2)
                })
            elif percentage < 60:
                weaknesses.append({
                    'course_id': score['course_id'],
                    'course_name': score['course_name'],
                    'avg_score': round(score['avg_score'], 2),
                    'percentage': round(percentage, 2)
                })
    
    conn.close()
    
    return {
        'strengths': strengths,
        'weaknesses': weaknesses
    }


def track_course_completion(student_id, course_id, completion_percentage=0, status='in_progress', estimated_time=None):
    """Track course completion for a student"""
    conn = get_db_connection()
    
    # Check if completion record already exists
    existing = conn.execute('''
        SELECT id FROM course_completions 
        WHERE student_id = ? AND course_id = ?
    ''', (student_id, course_id)).fetchone()
    
    if existing:
        # Update existing record
        conn.execute('''
            UPDATE course_completions 
            SET completion_percentage = ?, completion_status = ?, estimated_completion_time = ?
            WHERE student_id = ? AND course_id = ?
        ''', (completion_percentage, status, estimated_time, student_id, course_id))
    else:
        # Insert new record
        conn.execute('''
            INSERT INTO course_completions 
            (student_id, course_id, completion_percentage, completion_status, estimated_completion_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (student_id, course_id, completion_percentage, status, estimated_time))
    
    conn.commit()
    conn.close()


def mark_course_completed(student_id, course_id, completion_date=None):
    """Mark a course as completed and track improvement"""
    if completion_date is None:
        completion_date = datetime.now()
    
    conn = get_db_connection()
    
    # Update completion status
    conn.execute('''
        UPDATE course_completions 
        SET completion_status = 'completed', completion_date = ?
        WHERE student_id = ? AND course_id = ?
    ''', (completion_date, student_id, course_id))
    
    # Get initial and final scores for improvement calculation
    initial_score = conn.execute('''
        SELECT MIN(score) as initial_score 
        FROM scores 
        WHERE student_id = ? AND course_id = ?
    ''', (student_id, course_id)).fetchone()['initial_score']
    
    final_score = conn.execute('''
        SELECT MAX(score) as final_score 
        FROM scores 
        WHERE student_id = ? AND course_id = ?
    ''', (student_id, course_id)).fetchone()['final_score']
    
    if initial_score is not None and final_score is not None:
        improvement_percentage = ((final_score - initial_score) / initial_score * 100) if initial_score != 0 else 0
        
        # Insert improvement tracking record
        conn.execute('''
            INSERT INTO improvement_tracking 
            (student_id, course_id, initial_score, final_score, improvement_percentage, completion_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (student_id, course_id, initial_score, final_score, improvement_percentage, completion_date))
    
    conn.commit()
    conn.close()


def get_improvement_tracking(student_id):
    """Get improvement tracking data for a student"""
    conn = get_db_connection()
    
    # Get improvement tracking data
    improvements = conn.execute('''
        SELECT 
            c.course_name,
            i.initial_score,
            i.final_score,
            i.improvement_percentage,
            i.completion_date
        FROM improvement_tracking i
        JOIN courses c ON i.course_id = c.course_id
        WHERE i.student_id = ?
        ORDER BY i.completion_date DESC
    ''', (student_id,)).fetchall()
    
    conn.close()
    
    return [dict(improvement) for improvement in improvements]


def get_most_improved_students(limit=5):
    """Get the most improved students based on improvement percentage"""
    conn = get_db_connection()
    
    # Get students with highest improvement percentages
    most_improved = conn.execute('''
        SELECT 
            s.name,
            i.student_id,
            AVG(i.improvement_percentage) as avg_improvement,
            COUNT(i.course_id) as courses_improved
        FROM improvement_tracking i
        JOIN students s ON i.student_id = s.student_id
        GROUP BY i.student_id, s.name
        ORDER BY avg_improvement DESC
        LIMIT ?
    ''', (limit,)).fetchall()
    
    conn.close()
    
    return [dict(student) for student in most_improved]


def calculate_overall_improvement(student_id):
    """Calculate overall improvement for a student"""
    conn = get_db_connection()
    
    # Get all scores for the student ordered by time
    all_scores = conn.execute('''
        SELECT 
            s.score,
            s.attempt_timestamp,
            c.course_name
        FROM scores s
        JOIN courses c ON s.course_id = c.course_id
        WHERE s.student_id = ?
        ORDER BY s.attempt_timestamp
    ''', (student_id,)).fetchall()
    
    improvement_data = {
        'student_id': student_id,
        'total_improvement': 0,
        'improvement_percentage': 0,
        'courses_improved': 0,
        'courses_declined': 0,
        'overall_trend': 'stable'  # increasing, decreasing, stable
    }
    
    if all_scores:
        # Group scores by course to analyze improvement per course
        course_scores = {}
        for score in all_scores:
            course_name = score['course_name']
            if course_name not in course_scores:
                course_scores[course_name] = []
            course_scores[course_name].append(score)
        
        total_improvement = 0
        improvement_count = 0
        
        for course_name, scores in course_scores.items():
            if len(scores) > 1:  # Need at least 2 scores to calculate improvement
                first_score = scores[0]['score']
                last_score = scores[-1]['score']
                improvement = last_score - first_score
                
                total_improvement += improvement
                improvement_count += 1
                
                if improvement > 0:
                    improvement_data['courses_improved'] += 1
                else:
                    improvement_data['courses_declined'] += 1
        
        if improvement_count > 0:
            improvement_data['total_improvement'] = total_improvement
            improvement_data['improvement_percentage'] = (total_improvement / improvement_count) if improvement_count > 0 else 0
            
            if improvement_data['improvement_percentage'] > 5:
                improvement_data['overall_trend'] = 'increasing'
            elif improvement_data['improvement_percentage'] < -5:
                improvement_data['overall_trend'] = 'decreasing'
    
    conn.close()
    return improvement_data


@app.route('/reports/download/<report_type>')
def download_report(report_type):
    """Download reports in different formats"""
    format_type = request.args.get('format', 'pdf')
    student_id = request.args.get('student_id')
    
    if report_type == 'student' and student_id:
        return generate_student_report_download(student_id, format_type)
    elif report_type == 'class':
        return generate_class_report_download(format_type)
    elif report_type == 'improvement':
        return generate_improvement_report_download(format_type)
    elif report_type == 'pairing':
        return generate_pairing_report_download(format_type)
    elif report_type == 'recommendation':
        return generate_recommendation_report_download(format_type)
    elif report_type == 'all':
        return generate_all_data_download(format_type)
    else:
        return jsonify({'error': 'Invalid report type or missing parameters'}), 400


def generate_student_report_download(student_id, format_type):
    """Generate student report in specified format"""
    conn = get_db_connection()
    
    # Get student info
    student = conn.execute(
        'SELECT * FROM students WHERE student_id = ?', (student_id,)
    ).fetchone()
    
    # Get student scores
    scores = conn.execute('''
        SELECT c.course_name, sc.score, sc.max_score, sc.grade, sc.attempt_timestamp
        FROM scores sc
        JOIN courses c ON sc.course_id = c.course_id
        WHERE sc.student_id = ?
        ORDER BY sc.attempt_timestamp DESC
    ''', (student_id,)).fetchall()
    
    # Get student recommendations
    recommendations = conn.execute('''
        SELECT r.course_id, c.course_name, r.recommendation, r.priority
        FROM recommendations r
        JOIN courses c ON r.course_id = c.course_id
        WHERE r.student_id = ?
        ORDER BY 
            CASE r.priority
                WHEN 'High' THEN 1
                WHEN 'Medium' THEN 2
                WHEN 'Low' THEN 3
            END
    ''', (student_id,)).fetchall()
    
    # Get student improvement data
    improvements = get_improvement_tracking(student_id)
    
    conn.close()
    
    if format_type.lower() == 'pdf':
        return generate_student_pdf_report(student, scores, recommendations, improvements)
    elif format_type.lower() == 'excel':
        return generate_student_excel_report(student, scores, recommendations, improvements)
    elif format_type.lower() == 'csv':
        return generate_student_csv_report(student, scores, recommendations, improvements)
    else:
        return jsonify({'error': 'Unsupported format'}), 400


def generate_student_pdf_report(student, scores, recommendations, improvements):
    """Generate student report as PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create content
    content = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    content.append(Paragraph('Student Performance Report', title_style))
    
    # Student info
    content.append(Paragraph(f'<b>Student:</b> {student["name"]}', styles['Normal']))
    content.append(Paragraph(f'<b>Email:</b> {student["email"]}', styles['Normal']))
    content.append(Paragraph(f'<b>Student ID:</b> {student["student_id"]}', styles['Normal']))
    content.append(Spacer(1, 12))
    
    # Scores table
    if scores:
        content.append(Paragraph('Scores by Course', styles['Heading2']))
        
        # Prepare table data
        table_data = [['Course', 'Score', 'Max Score', 'Grade', 'Date']]
        for score in scores:
            table_data.append([
                score['course_name'],
                str(score['score']),
                str(score['max_score']),
                score['grade'],
                str(score['attempt_timestamp'])
            ])
        
        # Create table
        score_table = Table(table_data)
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(score_table)
        content.append(Spacer(1, 12))
    
    # Recommendations
    if recommendations:
        content.append(Paragraph('Course Recommendations', styles['Heading2']))
        
        # Prepare table data
        rec_table_data = [['Course', 'Recommendation', 'Priority']]
        for rec in recommendations:
            rec_table_data.append([
                rec['course_name'],
                rec['recommendation'],
                rec['priority']
            ])
        
        # Create table
        rec_table = Table(rec_table_data)
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(rec_table)
        content.append(Spacer(1, 12))
    
    # Improvements
    if improvements:
        content.append(Paragraph('Improvement Tracking', styles['Heading2']))
        
        # Prepare table data
        imp_table_data = [['Course', 'Initial Score', 'Final Score', 'Improvement %', 'Date']]
        for imp in improvements:
            imp_table_data.append([
                imp['course_name'],
                str(imp['initial_score']),
                str(imp['final_score']),
                f"{imp['improvement_percentage']:.2f}%",
                str(imp['completion_date'])
            ])
        
        # Create table
        imp_table = Table(imp_table_data)
        imp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(imp_table)
    
    # Build PDF
    doc.build(content)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'student_report_{student["student_id"]}.pdf',
        mimetype='application/pdf'
    )


def generate_student_excel_report(student, scores, recommendations, improvements):
    """Generate student report as Excel"""
    # Create a DataFrame for each section
    scores_df = pd.DataFrame(scores)
    recommendations_df = pd.DataFrame(recommendations)
    improvements_df = pd.DataFrame(improvements)
    
    # Create Excel file in memory
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Write student info as metadata
        metadata = pd.DataFrame({'Info': ['Student Name', 'Email', 'Student ID'], 
                                'Value': [student['name'], student['email'], student['student_id']]})
        metadata.to_excel(writer, sheet_name='Student Info', index=False)
        
        # Write scores
        if not scores_df.empty:
            scores_df.to_excel(writer, sheet_name='Scores', index=False)
        
        # Write recommendations
        if not recommendations_df.empty:
            recommendations_df.to_excel(writer, sheet_name='Recommendations', index=False)
        
        # Write improvements
        if not improvements_df.empty:
            improvements_df.to_excel(writer, sheet_name='Improvements', index=False)
    
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'student_report_{student["student_id"]}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


def generate_student_csv_report(student, scores, recommendations, improvements):
    """Generate student report as CSV (multiple files in ZIP)"""
    from zipfile import ZipFile
    
    # Create a ZIP file containing multiple CSVs
    buffer = io.BytesIO()
    with ZipFile(buffer, 'w') as zip_file:
        # Create CSV content for scores
        scores_df = pd.DataFrame(scores)
        if not scores_df.empty:
            scores_csv = scores_df.to_csv(index=False)
            zip_file.writestr(f'student_{student["student_id"]}_scores.csv', scores_csv)
        
        # Create CSV content for recommendations
        recommendations_df = pd.DataFrame(recommendations)
        if not recommendations_df.empty:
            rec_csv = recommendations_df.to_csv(index=False)
            zip_file.writestr(f'student_{student["student_id"]}_recommendations.csv', rec_csv)
        
        # Create CSV content for improvements
        improvements_df = pd.DataFrame(improvements)
        if not improvements_df.empty:
            imp_csv = improvements_df.to_csv(index=False)
            zip_file.writestr(f'student_{student["student_id"]}_improvements.csv', imp_csv)
        
        # Create a summary CSV
        summary_data = {
            'Student Name': [student['name']],
            'Email': [student['email']],
            'Student ID': [student['student_id']],
            'Total Scores': [len(scores)],
            'Total Recommendations': [len(recommendations)],
            'Total Improvements': [len(improvements)]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_csv = summary_df.to_csv(index=False)
        zip_file.writestr(f'student_{student["student_id"]}_summary.csv', summary_csv)
    
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'student_report_{student["student_id"]}.zip',
        mimetype='application/zip'
    )


def ml_performance_classification():
    """Use ML to classify student performance using clustering"""
    conn = get_db_connection()
    
    # Get all student scores
    data = conn.execute('''
        SELECT s.student_id, s.name, c.course_id, sc.score, sc.max_score
        FROM students s
        JOIN scores sc ON s.student_id = sc.student_id
        JOIN courses c ON sc.course_id = c.course_id
    ''').fetchall()
    
    conn.close()
    
    if not data:
        return {}
    
    # Create a pivot table of student scores by course
    df = pd.DataFrame(data)
    if df.empty:
        return {}
    
    # Create a pivot table with students as rows and courses as columns
    pivot_df = df.pivot_table(index='student_id', columns='course_id', values='score', fill_value=0)
    
    # Prepare features for clustering
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(pivot_df)
    
    # Apply K-means clustering to classify students
    n_clusters = min(3, len(pivot_df))  # Ensure we don't have more clusters than students
    if n_clusters > 1:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(scaled_data)
        
        # Create results dictionary
        results = {}
        for i, student_id in enumerate(pivot_df.index):
            cluster = cluster_labels[i]
            if cluster not in results:
                results[cluster] = []
            results[cluster].append(student_id)
        
        return results
    else:
        # If only one student, return as single cluster
        return {0: [pivot_df.index[0]] if len(pivot_df) > 0 else []}


def ml_improvement_prediction(student_id):
    """Use ML to predict improvement for a student"""
    conn = get_db_connection()
    
    # Get student scores with timestamps
    data = conn.execute('''
        SELECT s.score, s.max_score, s.attempt_timestamp
        FROM scores s
        WHERE s.student_id = ?
        ORDER BY s.attempt_timestamp
    ''', (student_id,)).fetchall()
    
    conn.close()
    
    if len(data) < 2:
        # Not enough data to make a prediction
        return {'prediction': 'Insufficient data for prediction', 'trend': 'unknown'}
    
    # Prepare data for linear regression
    scores = [row['score'] for row in data]
    timestamps = [i for i in range(len(data))]  # Use index as time
    
    # Convert to numpy arrays
    X = np.array(timestamps).reshape(-1, 1)
    y = np.array(scores)
    
    # Fit linear regression model
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict next score
    next_time = len(data)
    predicted_score = model.predict([[next_time]])[0]
    
    # Calculate trend
    slope = model.coef_[0]
    trend = 'improving' if slope > 0 else 'declining' if slope < 0 else 'stable'
    
    return {
        'predicted_score': predicted_score,
        'current_trend': trend,
        'slope': slope,
        'model_score': model.score(X, y)
    }


def ml_course_recommendation_ml(student_id):
    """Use ML-based content filtering for course recommendations"""
    conn = get_db_connection()
    
    # Get all student scores
    all_scores = conn.execute('''
        SELECT s.student_id, c.course_id, c.course_name, s.score, s.max_score
        FROM scores s
        JOIN courses c ON s.course_id = c.course_id
    ''').fetchall()
    
    # Get the specific student's scores
    student_scores = conn.execute('''
        SELECT c.course_id, c.course_name, s.score, s.max_score
        FROM scores s
        JOIN courses c ON s.course_id = c.course_id
        WHERE s.student_id = ?
    ''', (student_id,)).fetchall()
    
    conn.close()
    
    if not all_scores or not student_scores:
        return []
    
    # Create a student-course matrix
    df = pd.DataFrame(all_scores)
    matrix = df.pivot_table(index='student_id', columns='course_id', values='score', fill_value=0)
    
    if student_id not in matrix.index:
        return []
    
    # Get the current student's row
    student_row = matrix.loc[student_id].values.reshape(1, -1)
    
    # Calculate cosine similarity with all other students
    similarities = cosine_similarity(student_row, matrix.values)
    
    # Get the most similar students (excluding the current student)
    similar_students_idx = np.argsort(similarities[0])[::-1][1:6]  # Top 5 similar students
    
    # Find courses that similar students did well in but this student hasn't taken or did poorly in
    recommendations = []
    
    # Get courses the current student is weak in
    weak_courses = []
    for score in student_scores:
        if score['max_score'] > 0 and (score['score'] / score['max_score']) * 100 < 60:
            weak_courses.append(score['course_id'])
    
    # For each similar student, find courses they did well in
    for idx in similar_students_idx:
        similar_student_id = matrix.index[idx]
        
        # Get scores for this similar student
        similar_scores = df[df['student_id'] == similar_student_id]
        
        for _, score_row in similar_scores.iterrows():
            # If this student did well in a course that the target student is weak in
            if score_row['course_id'] in weak_courses:
                if score_row['score'] > 75:  # High performing course for similar student
                    recommendations.append({
                        'course_id': score_row['course_id'],
                        'course_name': score_row['course_name'],
                        'recommended_because': f'Similar students performed well in this course',
                        'similarity_score': similarities[0][idx]
                    })
    
    # Remove duplicates and return top recommendations
    unique_recs = []
    seen_courses = set()
    for rec in recommendations:
        if rec['course_id'] not in seen_courses:
            unique_recs.append(rec)
            seen_courses.add(rec['course_id'])
    
    return unique_recs[:5]  # Return top 5 recommendations


def ml_mentor_matching_ml(weak_student_id):
    """Use ML-based cosine similarity for mentor matching"""
    conn = get_db_connection()
    
    # Get all student scores to create a student-course matrix
    all_scores = conn.execute('''
        SELECT s.student_id, c.course_id, s.score
        FROM scores s
        JOIN courses c ON s.course_id = c.course_id
    ''').fetchall()
    
    conn.close()
    
    if not all_scores:
        return []
    
    # Create a student-course matrix
    df = pd.DataFrame(all_scores)
    matrix = df.pivot_table(index='student_id', columns='course_id', values='score', fill_value=0)
    
    if weak_student_id not in matrix.index:
        return []
    
    # Get the weak student's row
    weak_student_row = matrix.loc[weak_student_id].values.reshape(1, -1)
    
    # Calculate cosine similarity with all other students
    similarities = cosine_similarity(weak_student_row, matrix.values)
    
    # Get the most similar students (excluding the current student)
    similar_students_idx = np.argsort(similarities[0])[::-1][1:11]  # Top 10 similar students
    
    # Find potential mentors - students who perform well in courses where weak student struggles
    potential_mentors = []
    
    # Get courses where the weak student is struggling
    weak_student_scores = df[df['student_id'] == weak_student_id]
    weak_courses = []
    for _, score_row in weak_student_scores.iterrows():
        if score_row['max_score'] > 0 and (score_row['score'] / score_row['max_score']) * 100 < 60:
            weak_courses.append(score_row['course_id'])
    
    # For each similar student, check if they are strong in weak courses
    for idx in similar_students_idx:
        potential_mentor_id = matrix.index[idx]
        similarity_score = similarities[0][idx]
        
        # Check if this student is strong in the weak courses
        potential_mentor_scores = df[df['student_id'] == potential_mentor_id]
        strong_in_weak_courses = 0
        
        for _, score_row in potential_mentor_scores.iterrows():
            if score_row['course_id'] in weak_courses and score_row['score'] > 75:
                strong_in_weak_courses += 1
        
        if strong_in_weak_courses > 0:
            potential_mentors.append({
                'mentor_id': potential_mentor_id,
                'similarity_score': float(similarity_score),
                'courses_mentored': strong_in_weak_courses,
                'match_quality': float(similarity_score) * strong_in_weak_courses
            })
    
    # Sort by match quality and return top matches
    potential_mentors.sort(key=lambda x: x['match_quality'], reverse=True)
    return potential_mentors[:5]  # Return top 5 potential mentors


if __name__ == '__main__':
    init_db()
    app.run(debug=True)