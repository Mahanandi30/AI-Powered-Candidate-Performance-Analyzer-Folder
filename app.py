import os
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from database.models import db, Student, Attempt, Recommendation, MentorPairing, User
import pandas as pd

# Import new modular engines
from ml_engine.data_processor import DataProcessor
from ml_engine.performance_analyzer import PerformanceAnalyzer
from ml_engine.recommender import CourseRecommender
from ml_engine.mentor_matcher import MentorMatcher
from ml_engine.progress_tracker import ProgressTracker

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production' # Required for session
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///performance.db' # Changed to performance.db match requirements
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Initialize Engines
data_processor = DataProcessor()
performance_analyzer = PerformanceAnalyzer()
course_recommender = CourseRecommender()
mentor_matcher = MentorMatcher()
progress_tracker = ProgressTracker()

if not os.path.exists('uploads'):
    os.makedirs('uploads')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def create_default_admin():
    admin = User.query.filter_by(email='admin@college.edu').first()
    if not admin:
        hashed_pw = generate_password_hash('admin123', method='pbkdf2:sha256')
        new_admin = User(email='admin@college.edu', password=hashed_pw, role='admin')
        db.session.add(new_admin)
        db.session.commit()
        print("Default Admin Created.")

with app.app_context():
    db.create_all()
    create_default_admin()

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload_page')
@login_required
def upload_page():
    return render_template('index.html') # Renaming index.html to upload.html ideal, but reusing for flow

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    file = request.files['file']
    feedback_file = request.files.get('feedback_file')
    pairings_file = request.files.get('pairings_file')
    
    if file.filename == '':
        return redirect(request.url)
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        feedback_filepath = None
        if feedback_file and feedback_file.filename != '':
            feedback_filename = secure_filename(feedback_file.filename)
            feedback_filepath = os.path.join(app.config['UPLOAD_FOLDER'], feedback_filename)
            feedback_file.save(feedback_filepath)
        
        # Process Data using DataProcessor
        try:
            analyzed_df = data_processor.process_student_data(filepath, feedback_filepath)
            
            # Run Performance Analysis
            if 'performance' not in analyzed_df.columns:
                 analyzed_df['performance'] = analyzed_df['best_score'].apply(performance_analyzer.classify_performance)

            # Generate Recommendations
            analyzed_df['recommended_action'] = analyzed_df.apply(course_recommender.recommend_courses, axis=1)
            
            analyzed_df.to_csv('final_student_analysis.csv', index=False)
            
            # --- DATABASE PERSISTENCE (Partial Integration to meet ANAR requirements) ---
            # Ideally we iterate and save to DB here. For now keeping CSV flow as primary viewer
            # but ensuring User logic works.
            
            # Handle Pairings using MentorMatcher
            if pairings_file and pairings_file.filename != '':
                pairings_filename = secure_filename(pairings_file.filename)
                pairings_path = os.path.join(app.config['UPLOAD_FOLDER'], pairings_filename)
                pairings_file.save(pairings_path)
                pairings_df = data_processor.load_data(pairings_path)
                
                # Standardization
                cols = pairings_df.columns.str.lower()
                pairings_df.columns = cols
                rename_map = {}
                if 'course_id' in cols and 'course' not in cols: rename_map['course_id'] = 'course'
                if 'weak_student_name' in cols: rename_map['weak_student_name'] = 'mentee_name'
                if 'mentor_name' in cols: rename_map['mentor_name'] = 'mentor_name'
                if 'mentee' in cols: rename_map['mentee'] = 'mentee_name'
                if 'mentor' in cols: rename_map['mentor'] = 'mentor_name'
                
                pairings_df.rename(columns=rename_map, inplace=True)
                pairings_df.to_csv('mentor_pairings.csv', index=False)
            else:
                pairings = mentor_matcher.match_mentors_simple(analyzed_df)
                pairings.to_csv('mentor_pairings.csv', index=False)
            
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            return f"An error occurred: {e}"

@app.route('/dashboard')
@login_required
def dashboard():
    # Load data for display
    try:
        if os.path.exists('final_student_analysis.csv'):
            df = pd.read_csv('final_student_analysis.csv')
            students = df.head(100).to_dict('records')
            
            # Calculate Stats for Chart
            total_students = len(df)
            performance_counts = df['performance'].value_counts()
            high_performers = performance_counts.get('High', 0)
            medium_performers = performance_counts.get('Medium', 0)
            poor_performers = performance_counts.get('Poor', 0)
            
            # Additional Stats for new Graphs
            course_dist = df['course_name'].value_counts().to_dict()
            avg_score_course = df.groupby('course_name')['best_score'].mean().to_dict()
            
            # Top 5 and Bottom 5 Performers
            top_performers = df.nlargest(5, 'best_score').to_dict('records')
            bottom_performers = df.nsmallest(5, 'best_score').to_dict('records')
            
            # Course Analytics Grid Data
            course_analytics = []
            for course, group in df.groupby('course_name'):
                avg = group['best_score'].mean()
                pass_count = group[group['best_score'] >= 50].shape[0] # Assuming 50 is pass
                total = group.shape[0]
                pass_rate = (pass_count / total * 100) if total > 0 else 0
                difficulty = 'High' if avg < 60 else ('Medium' if avg < 80 else 'Low')
                course_analytics.append({
                    'name': course,
                    'avg_score': round(avg, 1),
                    'pass_rate': round(pass_rate, 1),
                    'difficulty': difficulty
                })
            
        else:
            students = []
            total_students = 0
            high_performers = 0
            medium_performers = 0
            poor_performers = 0
            course_dist = {}
            avg_score_course = {}
            top_performers = []
            bottom_performers = []
            course_analytics = []
            
        if os.path.exists('mentor_pairings.csv'):
            pairings = pd.read_csv('mentor_pairings.csv').to_dict('records')
        else:
            pairings = []
            
        return render_template('dashboard.html', 
                               students=students, 
                               pairings=pairings,
                               total_students=total_students,
                               high_performers=high_performers,
                               medium_performers=medium_performers,
                               poor_performers=poor_performers,
                               course_dist=course_dist,
                               avg_score_course=avg_score_course,
                               top_performers=top_performers,
                               bottom_performers=bottom_performers,
                               course_analytics=course_analytics,
                               user=current_user)
    except Exception as e:
         return f"Error loading dashboard: {e}"

@app.route('/feedback')
@login_required
def view_feedback():
    feedback_by_course = {}
    if os.path.exists('final_student_analysis.csv'):
        df = pd.read_csv('final_student_analysis.csv')
        # Check which column holds the course identifier
        course_col = 'course_name' if 'course_name' in df.columns else ('course' if 'course' in df.columns else None)
        
        if course_col:
            for course, group in df.groupby(course_col):
                feedback_by_course[course] = group.to_dict('records')
        else:
             # Fallback
             feedback_by_course['General'] = df.to_dict('records')
    
    return render_template('feedback.html', feedback_by_course=feedback_by_course)

@app.route('/student/<email>')
@login_required
def student_analysis(email):
    # Mock data retrieval for demonstration (replace with DB query)
    student = {'name': 'Student Name', 'email': email, 'performance_category': 'Medium'}
    analysis = {'strengths': ['Python', 'SQL'], 'weaknesses': ['Math']}
    recommendations = ['Advanced Stats']
    attempts = [{'course': 'Python', 'score': 80, 'grade': 'A', 'attempt': 1}]
    
    # Try to find meaningful data from CSV if exists
    if os.path.exists('final_student_analysis.csv'):
        df = pd.read_csv('final_student_analysis.csv')
        row = df[df['email'] == email]
        if not row.empty:
            r = row.iloc[0]
            student = {
                'name': r['name'], 
                'email': r['email'], 
                'performance_category': r['performance']
            }
            # Mock parsing strengths from a column if it existed
            analysis = {'strengths': [], 'weaknesses': []} 
            recommendations = [r.get('recommended_action', 'None')]

    # Get Detailed History & Analyze Strengths/Weaknesses
    if os.path.exists('detailed_student_analysis.csv'):
        detailed_df = pd.read_csv('detailed_student_analysis.csv')
        student_history = detailed_df[detailed_df['email'] == email]
        
        if not student_history.empty:
            # Sort by entry if meaningful, else just use index
            attempts = student_history.to_dict('records')
            
            # Normalize keys for template (ensure 'score' exists)
            for i, attempt in enumerate(attempts):
                if 'score' not in attempt:
                    # Fallbacks based on common column names
                    attempt['score'] = attempt.get('mark', attempt.get('best_score', 0))
                
                if 'attempt' not in attempt:
                    attempt['attempt'] = i + 1
                    
            # Real AI Analysis
            analysis = performance_analyzer.analyze_strengths_weaknesses(student_history)
            
            # Recommendation Engine
            if analysis['weaknesses']:
                recommendations = course_recommender.recommend_from_weaknesses(analysis['weaknesses'])
            else:
                 recommendations = ["Keep maintaining your high performance!", "Mentor peers in your strong subjects."]

                    
    return render_template('analysis.html', student=student, analysis=analysis, recommendations=recommendations, attempts=attempts)

@app.route('/pairings')
@login_required
def view_pairings():
    pairings_by_course = {}
    if os.path.exists('mentor_pairings.csv'):
        df = pd.read_csv('mentor_pairings.csv')
        if not df.empty and 'course' in df.columns:
            # Group by course
            for course, group in df.groupby('course'):
                pairings_by_course[course] = group.to_dict('records')
        elif not df.empty:
             # Fallback if no course column, put all in 'General'
             pairings_by_course['General'] = df.to_dict('records')
    
    return render_template('pairing.html', pairings_by_course=pairings_by_course)
    
@app.route('/download_report')
@login_required
def download_report():
    if os.path.exists('final_student_analysis.csv'):
        return send_file('final_student_analysis.csv', as_attachment=True)
    return "Report not available."

def refresh_analysis():
    """
    Helper to re-process detailed data and update final analysis CSV.
    Ensures dashboard consistency after CRUD operations.
    """
    try:
        if os.path.exists('detailed_student_analysis.csv'):
            # Process the updated detailed file to regenerate summary
            analyzed_df = data_processor.process_student_data('detailed_student_analysis.csv')
            
            # Run Performance Analysis
            if 'performance' not in analyzed_df.columns:
                 analyzed_df['performance'] = analyzed_df['best_score'].apply(performance_analyzer.classify_performance)

            # Generate Recommendations
            analyzed_df['recommended_action'] = analyzed_df.apply(course_recommender.recommend_courses, axis=1)
            
            # Save Updated Final Analysis
            analyzed_df.to_csv('final_student_analysis.csv', index=False)
            return True
    except Exception as e:
        print(f"Error refreshing analysis: {e}")
        return False

@app.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        try:
            # Extract Form Data
            new_data = {
                'name': request.form.get('name'),
                'email': request.form.get('email'),
                'course_name': request.form.get('course_name'),
                'score': float(request.form.get('score')),
                'attempt_timestamp': request.form.get('attempt_timestamp'),
                'feedback': request.form.get('feedback', ''),
                'topic_tags': request.form.get('topic_tags', '')
            }
            
            # Load existing detailed data or create new
            if os.path.exists('detailed_student_analysis.csv'):
                df = pd.read_csv('detailed_student_analysis.csv')
            else:
                df = pd.DataFrame(columns=new_data.keys())
            
            # Append new record
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
            df.to_csv('detailed_student_analysis.csv', index=False)
            
            # Trigger Refresh
            refresh_analysis()
            
            flash(f"Student {new_data['name']} added successfully!", 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f"Error adding student: {str(e)}", 'danger')
            return redirect(url_for('add_student'))
            
    return render_template('add_student.html')

@app.route('/edit_student/<email>', methods=['GET', 'POST'])
@login_required
def edit_student(email):
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            score = float(request.form.get('score'))
            
            if os.path.exists('detailed_student_analysis.csv'):
                df = pd.read_csv('detailed_student_analysis.csv')
                
                # 1. Update Name for ALL records of this student
                df.loc[df['email'] == email, 'name'] = name
                
                # 2. Update Score for the LATEST record
                student_rows = df[df['email'] == email]
                if not student_rows.empty:
                    # Identify latest by timestamp or index
                    if 'attempt_timestamp' in df.columns:
                        df['attempt_timestamp'] = pd.to_datetime(df['attempt_timestamp'], errors='coerce')
                        latest_idx = df[df['email'] == email].sort_values('attempt_timestamp').index[-1]
                    else:
                        latest_idx = student_rows.index[-1]
                        
                    df.at[latest_idx, 'score'] = score
                
                df.to_csv('detailed_student_analysis.csv', index=False)
                refresh_analysis()
                
                flash(f"Student record updated successfully.", 'success')
                return redirect(url_for('dashboard'))
            else:
                 flash("No data found to edit.", 'warning')

        except Exception as e:
            flash(f"Error editing student: {str(e)}", 'danger')
            
    # GET Request: Populate Form
    student = {'email': email, 'name': '', 'latest_score': 0}
    latest_attempt = {}
    
    if os.path.exists('detailed_student_analysis.csv'):
        df = pd.read_csv('detailed_student_analysis.csv')
        student_rows = df[df['email'] == email]
        
        if not student_rows.empty:
            # Get Name from first row
            student['name'] = student_rows.iloc[0]['name']
            
            # Get Latest Attempt
            if 'attempt_timestamp' in df.columns:
                df['attempt_timestamp'] = pd.to_datetime(df['attempt_timestamp'], errors='coerce')
                latest_row = student_rows.sort_values('attempt_timestamp').iloc[-1]
            else:
                latest_row = student_rows.iloc[-1]
            
            latest_attempt = {
                'course_name': latest_row.get('course_name', 'Unknown'),
                'score': latest_row.get('score', 0),
                'attempt_timestamp': latest_row.get('attempt_timestamp', 'Unknown')
            }

    return render_template('edit_student.html', student=student, latest_attempt=latest_attempt)

@app.route('/delete_student/<email>', methods=['POST'])
@login_required
def delete_student(email):
    try:
        # Update Detailed History (Source of Truth)
        if os.path.exists('detailed_student_analysis.csv'):
            detailed_df = pd.read_csv('detailed_student_analysis.csv')
            detailed_df = detailed_df[detailed_df['email'] != email]
            detailed_df.to_csv('detailed_student_analysis.csv', index=False)
            
            # Refresh Final Summary based on new detailed data
            refresh_analysis()
            
            flash(f'Student {email} deleted successfully.', 'success')
        else:
            flash('No data found to delete.', 'warning')
            
    except Exception as e:
        flash(f'Error deleting student: {str(e)}', 'danger')
        
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
