# AI-Powered Candidate Performance Analyzer

## Overview
The AI-Powered Candidate Performance Analyzer is a comprehensive web-based system designed to help educational institutions analyze student performance, identify strengths and weaknesses, recommend courses for improvement, pair students with mentors, and track progress over time. The system leverages machine learning algorithms to provide intelligent insights and recommendations.

## Features
- **Data Management**: Upload and process student performance data from CSV and Excel files
- **Performance Analysis**: Identify student strengths and weaknesses using ML algorithms
- **Course Recommendations**: Intelligent course recommendations based on weak areas
- **Mentor Pairing**: Smart mentor-mentee matching based on performance compatibility
- **Progress Tracking**: Monitor student improvement over time
- **Dashboard**: Real-time visualization of class performance
- **Reporting**: Generate comprehensive reports in multiple formats (PDF, Excel, CSV)
- **ML Algorithms**: K-means clustering, linear regression, cosine similarity

## Technology Stack
- **Backend**: Python 3.7+, Flask web framework
- **Database**: SQLite for data persistence
- **ML Libraries**: scikit-learn, pandas, numpy
- **Frontend**: HTML, CSS, JavaScript with Bootstrap
- **Visualization**: Plotly for interactive charts
- **Document Generation**: ReportLab for PDF reports

## Installation

1. Clone the repository or download the project files
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Running the Application
```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Data Upload
1. Navigate to the Upload Data page
2. Upload a CSV or Excel file containing student performance data
3. Ensure your file contains the following required columns:
   - student_id
   - name
   - email
   - course_id
   - course_name
   - attempt_id
   - attempt_timestamp
   - score
   - max_score
   - grade

### Features Overview
- **Dashboard**: View overall class performance metrics and visualizations
- **Students**: Analyze individual student performance
- **Recommendations**: View course recommendations for students
- **Mentor Pairings**: See mentor-mentee pairings
- **Progress Tracking**: Monitor student improvement over time
- **Reports**: Generate detailed reports in various formats

## Database Schema

The application uses SQLite with the following tables:

- **students**: Stores student information (ID, name, email)
- **courses**: Stores course information (ID, name)
- **scores**: Stores student scores with timestamps
- **recommendations**: Stores course recommendations for students
- **pairings**: Stores mentor-mentee pairings with compatibility scores
- **course_completions**: Tracks course completion status
- **improvement_tracking**: Tracks improvement metrics

## API Endpoints

- `GET /api/analytics` - Get overall class analytics
- `GET /api/student/<student_id>` - Get specific student data
- `GET /api/ml/performance-classification` - Get ML-based performance classification
- `GET /api/ml/improvement-prediction/<student_id>` - Get improvement predictions
- `GET /api/ml/recommendations/<student_id>` - Get ML-based recommendations
- `GET /api/ml/mentors/<student_id>` - Get ML-based mentor matches
- `GET /api/progress/<student_id>` - Get student progress data
- `GET /api/improvement/most-improved` - Get most improved students
- `POST /api/progress/track` - Track course progress
- `POST /api/progress/complete` - Mark course as completed

## Machine Learning Algorithms

### Performance Classification
- **K-means clustering**: Groups students based on performance patterns
- **StandardScaler**: Normalizes features before clustering

### Course Recommendations
- **Content-based filtering**: Uses cosine similarity to find similar students
- **Focus on weak areas**: Recommends courses where student is weak but similar students excel

### Mentor Matching
- **Cosine similarity**: Calculates compatibility between students
- **Course-specific analysis**: Matches based on performance in specific courses

### Improvement Prediction
- **Linear regression**: Predicts future performance trends
- **Time series analysis**: Tracks improvement over time

## Project Structure

```
AI-Powered-Candidate-Performance-Analyzer-Folder/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md            # Project documentation
├── presentation_outline.md # Presentation slides outline
├── test_app.py          # Unit tests
├── src/                 # Source code (if any)
├── models/              # ML models (if any)
├── utils/               # Utility functions
├── static/              # Static files (CSS, JS, images)
├── templates/           # HTML templates
│   ├── base.html        # Base template
│   ├── index.html       # Home page
│   ├── dashboard.html   # Dashboard page
│   ├── upload.html      # Data upload page
│   ├── students.html    # Students analysis page
│   ├── recommendations.html # Recommendations page
│   ├── pairings.html    # Mentor pairing page
│   ├── reports.html     # Reports page
│   └── student_progress.html # Student progress page
└── uploads/             # Uploaded files storage
```

## Testing

The project includes a comprehensive test suite in `test_app.py` that covers:

- API endpoint testing
- ML algorithm functionality
- Database operations
- Data validation
- Performance analysis functions
- Progress tracking features

To run tests:
```bash
python test_app.py
```

## Deployment

### Local Deployment
1. Ensure all dependencies are installed
2. Run `python app.py`
3. Access the application at `http://localhost:5000`

### Production Deployment
For production deployment, consider:
- Using a production WSGI server like Gunicorn
- Setting up a reverse proxy with Nginx
- Using a production database like PostgreSQL
- Implementing proper logging and monitoring

Example with Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is created for educational purposes.

## Support

For support, please contact the development team or create an issue in the repository.