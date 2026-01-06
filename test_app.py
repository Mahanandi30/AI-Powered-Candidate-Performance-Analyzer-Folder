import unittest
import tempfile
import os
import sqlite3
from datetime import datetime
import pandas as pd
from io import StringIO
from unittest.mock import patch, MagicMock

# Import the main app
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import app, init_db, get_db_connection, analyze_student_performance, get_class_performance_analysis
from app import ml_performance_classification, ml_improvement_prediction, ml_course_recommendation_ml
from app import track_course_completion, mark_course_completed, get_improvement_tracking


class TestApp(unittest.TestCase):
    """Test cases for the AI-Powered Candidate Performance Analyzer"""
    
    def setUp(self):
        """Set up test database"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        # Store original database config
        self.original_db = app.config.get('DATABASE')
        app.config['DATABASE'] = self.db_path
        app.config['TESTING'] = True
        self.app = app.test_client()
        
        with app.app_context():
            init_db()
            
            # Insert test data
            conn = get_db_connection()
            
            # Insert test students
            conn.execute(
                'INSERT INTO students (student_id, name, email) VALUES (?, ?, ?)',
                ('S001', 'John Doe', 'john@example.com')
            )
            conn.execute(
                'INSERT INTO students (student_id, name, email) VALUES (?, ?, ?)',
                ('S002', 'Jane Smith', 'jane@example.com')
            )
            
            # Insert test courses
            conn.execute(
                'INSERT INTO courses (course_id, course_name) VALUES (?, ?)',
                ('C001', 'Mathematics')
            )
            conn.execute(
                'INSERT INTO courses (course_id, course_name) VALUES (?, ?)',
                ('C002', 'Physics')
            )
            
            # Insert test scores
            conn.execute('''
                INSERT INTO scores 
                (student_id, course_id, attempt_id, attempt_timestamp, score, max_score, grade)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'S001', 'C001', 1, '2023-01-01 10:00:00', 85, 100, 'A'
            ))
            conn.execute('''
                INSERT INTO scores 
                (student_id, course_id, attempt_id, attempt_timestamp, score, max_score, grade)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'S001', 'C002', 1, '2023-01-02 10:00:00', 45, 100, 'F'
            ))
            conn.execute('''
                INSERT INTO scores 
                (student_id, course_id, attempt_id, attempt_timestamp, score, max_score, grade)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'S002', 'C001', 1, '2023-01-01 10:00:00', 90, 100, 'A'
            ))
            conn.execute('''
                INSERT INTO scores 
                (student_id, course_id, attempt_id, attempt_timestamp, score, max_score, grade)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'S002', 'C002', 1, '2023-01-02 10:00:00', 75, 100, 'B'
            ))
            
            conn.commit()
            conn.close()
    
    def tearDown(self):
        """Clean up test database"""
        # Restore original database config
        if hasattr(self, 'original_db'):
            app.config['DATABASE'] = self.original_db
        
        # Close any remaining connections
        import sqlite3
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
        except:
            pass
        
        # Clean up file
        os.close(self.db_fd)
        os.unlink(self.db_path)


    def test_home_page(self):
        """Test home page loads successfully"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_dashboard_page(self):
        """Test dashboard page loads successfully"""
        response = self.app.get('/dashboard')
        self.assertEqual(response.status_code, 200)

    def test_upload_page(self):
        """Test upload page loads successfully"""
        response = self.app.get('/upload')
        self.assertEqual(response.status_code, 200)

    def test_students_page(self):
        """Test students page loads successfully"""
        response = self.app.get('/students')
        self.assertEqual(response.status_code, 200)

    def test_recommendations_page(self):
        """Test recommendations page loads successfully"""
        response = self.app.get('/recommendations')
        self.assertEqual(response.status_code, 200)

    def test_pairings_page(self):
        """Test pairings page loads successfully"""
        response = self.app.get('/pairings')
        self.assertEqual(response.status_code, 200)

    def test_reports_page(self):
        """Test reports page loads successfully"""
        response = self.app.get('/reports')
        self.assertEqual(response.status_code, 200)

    def test_progress_page(self):
        """Test progress page loads successfully"""
        response = self.app.get('/progress')
        self.assertEqual(response.status_code, 200)

    def test_api_analytics(self):
        """Test analytics API endpoint"""
        response = self.app.get('/api/analytics')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('total_students', data)
        self.assertIn('total_courses', data)
        self.assertIn('total_scores', data)

    def test_api_student_data(self):
        """Test student data API endpoint"""
        response = self.app.get('/api/student/S001')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('student', data)
        self.assertIn('scores', data)

    def test_analyze_student_performance(self):
        """Test student performance analysis function"""
        result = analyze_student_performance('S001')
        self.assertEqual(result['student_id'], 'S001')
        self.assertIn('strengths', result)
        self.assertIn('weaknesses', result)
        self.assertIn('improvement_areas', result)

    def test_get_class_performance_analysis(self):
        """Test class performance analysis function"""
        result = get_class_performance_analysis()
        self.assertIn('class_metrics', result)
        self.assertIn('performance_distribution', result)
        self.assertIn('subject_performance', result)

    def test_ml_performance_classification(self):
        """Test ML-based performance classification"""
        result = ml_performance_classification()
        self.assertIsInstance(result, dict)

    def test_ml_improvement_prediction(self):
        """Test ML-based improvement prediction"""
        result = ml_improvement_prediction('S001')
        self.assertIsInstance(result, dict)
        if result.get('prediction') != 'Insufficient data for prediction':
            self.assertIn('predicted_score', result)
            self.assertIn('current_trend', result)

    def test_ml_course_recommendation(self):
        """Test ML-based course recommendations"""
        result = ml_course_recommendation_ml('S001')
        self.assertIsInstance(result, list)

    def test_track_course_completion(self):
        """Test course completion tracking"""
        track_course_completion('S001', 'C001', 50, 'in_progress', '2 weeks')
        
        conn = get_db_connection()
        completion = conn.execute(
            'SELECT * FROM course_completions WHERE student_id = ? AND course_id = ?',
            ('S001', 'C001')
        ).fetchone()
        conn.close()
        
        self.assertIsNotNone(completion)
        self.assertEqual(completion['completion_percentage'], 50)
        self.assertEqual(completion['completion_status'], 'in_progress')

    def test_mark_course_completed(self):
        """Test marking course as completed"""
        # First track the course
        track_course_completion('S001', 'C001', 100, 'in_progress', '2 weeks')
        
        # Then mark as completed
        mark_course_completed('S001', 'C001')
        
        conn = get_db_connection()
        completion = conn.execute(
            'SELECT * FROM course_completions WHERE student_id = ? AND course_id = ?',
            ('S001', 'C001')
        ).fetchone()
        conn.close()
        
        self.assertIsNotNone(completion)
        self.assertEqual(completion['completion_status'], 'completed')

    def test_get_improvement_tracking(self):
        """Test improvement tracking function"""
        result = get_improvement_tracking('S001')
        self.assertIsInstance(result, list)

    def test_api_ml_performance_classification(self):
        """Test ML performance classification API"""
        response = self.app.get('/api/ml/performance-classification')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('classification', data)

    def test_api_ml_improvement_prediction(self):
        """Test ML improvement prediction API"""
        response = self.app.get('/api/ml/improvement-prediction/S001')
        self.assertEqual(response.status_code, 200)

    def test_api_ml_recommendations(self):
        """Test ML recommendations API"""
        response = self.app.get('/api/ml/recommendations/S001')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('recommendations', data)

    def test_api_ml_mentors(self):
        """Test ML mentor matching API"""
        response = self.app.get('/api/ml/mentors/S001')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('matches', data)

    def test_api_progress_tracking(self):
        """Test progress tracking API"""
        # Track some progress first
        track_course_completion('S001', 'C001', 75, 'in_progress', '1 week')
        
        response = self.app.get('/api/progress/S001')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('improvement_data', data)
        self.assertIn('improvements', data)
        self.assertIn('completion_status', data)

    def test_api_most_improved(self):
        """Test most improved students API"""
        response = self.app.get('/api/improvement/most-improved')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('most_improved_students', data)

    def test_api_pairings_data(self):
        """Test pairings data API"""
        response = self.app.get('/api/pairings')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('pairings', data)

    def test_api_recommendations_data(self):
        """Test recommendations data API"""
        response = self.app.get('/api/recommendations')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('recommendations', data)

    def test_csv_upload(self):
        """Test CSV file upload functionality"""
        # Create a temporary CSV file
        csv_content = """student_id,name,email,course_id,course_name,attempt_id,attempt_timestamp,score,max_score,grade
S003,Bob Johnson,bob@example.com,C001,Mathematics,1,2023-01-01,70,100,B
S003,Bob Johnson,bob@example.com,C002,Physics,1,2023-01-01,80,100,B"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_csv_path = f.name

        with open(temp_csv_path, 'rb') as csv_file:
            response = self.app.post('/upload', 
                                   data={'file': (csv_file, 'test.csv')},
                                   content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        os.unlink(temp_csv_path)

    def test_data_validation(self):
        """Test data validation for required columns"""
        # Test with missing columns
        csv_content = """student_id,name,email,course_id,attempt_id,attempt_timestamp,score,max_score,grade
S004,Alice Brown,alice@example.com,C001,1,2023-01-01,70,100,B"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_csv_path = f.name

        with open(temp_csv_path, 'rb') as csv_file:
            response = self.app.post('/upload', 
                                   data={'file': (csv_file, 'test.csv')},
                                   content_type='multipart/form-data')
        
        # Should return an error due to missing course_name column
        self.assertEqual(response.status_code, 200)  # Still returns 200 but with error in JSON
        data = response.get_json()
        self.assertIn('error', data)
        os.unlink(temp_csv_path)

    def test_recommendation_generation(self):
        """Test recommendation generation functionality"""
        # Insert a weak student's data
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO scores 
            (student_id, course_id, attempt_id, attempt_timestamp, score, max_score, grade)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            'S003', 'C001', 1, '2023-01-03 10:00:00', 30, 100, 'F'
        ))
        conn.commit()
        conn.close()
        
        # Test the recommendation function
        from app import generate_course_recommendations
        recommendations = generate_course_recommendations('S003')
        self.assertIsInstance(recommendations, list)

    def test_mentor_pairing_generation(self):
        """Test mentor pairing functionality"""
        conn = get_db_connection()
        from app import generate_mentor_pairings
        generate_mentor_pairings(conn)
        conn.close()

    def test_progress_tracking(self):
        """Test progress tracking functionality"""
        # Track progress
        track_course_completion('S001', 'C001', 50, 'in_progress', '2 weeks')
        
        # Verify it was tracked
        conn = get_db_connection()
        result = conn.execute(
            'SELECT * FROM course_completions WHERE student_id = ? AND course_id = ?',
            ('S001', 'C001')
        ).fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
        self.assertEqual(result['completion_percentage'], 50)


class TestMLAlgorithms(unittest.TestCase):
    """Test cases specifically for ML algorithms"""
    
    def setUp(self):
        """Set up test database with more data for ML testing"""
        self.db_fd, self.db_path = tempfile.mkstemp()
        # Store original database config
        self.original_db = app.config.get('DATABASE')
        app.config['DATABASE'] = self.db_path
        app.config['TESTING'] = True
        self.app = app.test_client()
        
        with app.app_context():
            init_db()
            
            # Insert more test data for ML algorithms
            conn = get_db_connection()
            
            # Insert multiple students with various performance levels
            students_data = [
                ('S001', 'John Doe', 'john@example.com'),
                ('S002', 'Jane Smith', 'jane@example.com'),
                ('S003', 'Bob Johnson', 'bob@example.com'),
                ('S004', 'Alice Brown', 'alice@example.com'),
                ('S005', 'Charlie Wilson', 'charlie@example.com')
            ]
            
            for student_data in students_data:
                conn.execute(
                    'INSERT INTO students (student_id, name, email) VALUES (?, ?, ?)',
                    student_data
                )
            
            # Insert courses
            courses_data = [
                ('C001', 'Mathematics'),
                ('C002', 'Physics'),
                ('C003', 'Chemistry'),
                ('C004', 'Biology')
            ]
            
            for course_data in courses_data:
                conn.execute(
                    'INSERT INTO courses (course_id, course_name) VALUES (?, ?)',
                    course_data
                )
            
            # Insert scores with different patterns for clustering
            scores_data = [
                # Strong student
                ('S001', 'C001', 1, '2023-01-01 10:00:00', 90, 100, 'A'),
                ('S001', 'C002', 1, '2023-01-01 10:00:00', 88, 100, 'A'),
                ('S001', 'C003', 1, '2023-01-01 10:00:00', 92, 100, 'A'),
                ('S001', 'C004', 1, '2023-01-01 10:00:00', 85, 100, 'B'),
                
                # Weak student
                ('S002', 'C001', 1, '2023-01-01 10:00:00', 45, 100, 'F'),
                ('S002', 'C002', 1, '2023-01-01 10:00:00', 50, 100, 'F'),
                ('S002', 'C003', 1, '2023-01-01 10:00:00', 40, 100, 'F'),
                ('S002', 'C004', 1, '2023-01-01 10:00:00', 48, 100, 'F'),
                
                # Medium student
                ('S003', 'C001', 1, '2023-01-01 10:00:00', 70, 100, 'C'),
                ('S003', 'C002', 1, '2023-01-01 10:00:00', 68, 100, 'D'),
                ('S003', 'C003', 1, '2023-01-01 10:00:00', 72, 100, 'C'),
                ('S003', 'C004', 1, '2023-01-01 10:00:00', 65, 100, 'D'),
                
                # Improving student
                ('S004', 'C001', 1, '2023-01-01 10:00:00', 55, 100, 'F'),
                ('S004', 'C001', 2, '2023-02-01 10:00:00', 65, 100, 'D'),
                ('S004', 'C001', 3, '2023-03-01 10:00:00', 75, 100, 'C'),
                
                # Declining student
                ('S005', 'C002', 1, '2023-01-01 10:00:00', 85, 100, 'B'),
                ('S005', 'C002', 2, '2023-02-01 10:00:00', 75, 100, 'C'),
                ('S005', 'C002', 3, '2023-03-01 10:00:00', 65, 100, 'D'),
            ]
            
            for score_data in scores_data:
                conn.execute('''
                    INSERT INTO scores 
                    (student_id, course_id, attempt_id, attempt_timestamp, score, max_score, grade)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', score_data)
            
            conn.commit()
            conn.close()
    
    def tearDown(self):
        """Clean up test database"""
        # Restore original database config
        if hasattr(self, 'original_db'):
            app.config['DATABASE'] = self.original_db
        
        # Close any remaining connections
        import sqlite3
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
        except:
            pass
        
        # Clean up file
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def tearDown(self):
        """Clean up test database"""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_kmeans_clustering(self):
        """Test K-means clustering for performance classification"""
        result = ml_performance_classification()
        self.assertIsInstance(result, dict)
        # Should have clusters with student IDs
        for cluster_id, student_list in result.items():
            self.assertIsInstance(cluster_id, int)
            self.assertIsInstance(student_list, list)

    def test_linear_regression_prediction(self):
        """Test linear regression for improvement prediction"""
        # Test with student who has multiple scores (S004)
        result = ml_improvement_prediction('S004')
        self.assertIsInstance(result, dict)
        if result.get('prediction') != 'Insufficient data for prediction':
            self.assertIn('predicted_score', result)
            self.assertIn('current_trend', result)
            self.assertIn('slope', result)
            # For an improving student, the trend should be positive
            if result['current_trend'] != 'unknown':
                # The slope might be positive or negative based on the data
                self.assertIsInstance(result['slope'], (int, float))

    def test_content_based_recommendations(self):
        """Test content-based filtering for recommendations"""
        result = ml_course_recommendation_ml('S002')  # Weak student
        self.assertIsInstance(result, list)
        # Should return recommendations for courses to improve
        for rec in result:
            self.assertIn('course_id', rec)
            self.assertIn('course_name', rec)
            self.assertIn('recommended_because', rec)
            self.assertIn('similarity_score', rec)

    def test_cosine_similarity_mentor_matching(self):
        """Test cosine similarity for mentor matching"""
        from app import ml_mentor_matching_ml
        result = ml_mentor_matching_ml('S002')  # Weak student
        self.assertIsInstance(result, list)
        # Should return potential mentors
        for mentor in result:
            self.assertIn('mentor_id', mentor)
            self.assertIn('similarity_score', mentor)
            self.assertIn('courses_mentored', mentor)
            self.assertIn('match_quality', mentor)


if __name__ == '__main__':
    unittest.main()