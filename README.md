# AI-Powered Candidate Performance Analyzer (CPA Tool)

## 📌 Project Overview
The **AI-Powered Candidate Performance Analyzer** is an advanced analytics platform designed to transform raw student performance data into actionable insights. By leveraging Machine Learning algorithms, the tool automatically identifies student strengths and weaknesses, recommends targeted remedial courses, and facilitates peer mentorship through smart pairing. It provides a real-time dashboard for educators to monitor class health and identify at-risk students instantly.

---

## 🛠️ Implementation Journey
The development of this project followed a structured, iterative approach to ensure robustness and scalability:

### Phase 1: Foundation & Data Processing
- **Goal**: Establish a reliable pipeline to ingest and clean heterogeneous data.
- **Action**: Built `ml_engine/data_processor.py` to handle CSV/Excel uploads, normalize column names dynamically, and manage missing values.
- **Result**: A robust data ingestion layer capable of processing diverse datasets.

### Phase 2: ML Engine Development
- **Goal**: Move beyond simple aggregations to intelligent analysis.
- **Action**:
    - Developed `PerformanceAnalyzer` to classify students using both average scores and **Consistency Metrics (Standard Deviation)**.
    - Implemented `CourseRecommender` with a specialized catalog to map weaknesses (e.g., "SQL") to remedial actions (e.g., "Database Design Course").
    - Created `MentorMatcher` to algorithmically pair "Weak" students with "Strong" mentors in the same subject area.

### Phase 3: Dashboard & Visualization
- **Goal**: Present complex data in an intuitive, actionable interface.
- **Action**:
    - Designed `dashboard.html` with real-time Chart.js visualizatons.
    - Implemented "Top 5 Honor Roll" and "Needs Attention" tables with Trend Indicators.
    - Added a **Subject-wise Performance Grid** to highlight course difficulty.

### Phase 4: Refinement & Polishing
- **Goal**: Enhance user experience and depth of insight.
- **Action**:
    - Integrated **Trend Analysis** (`latest_score` vs `average_score`) to detect improvement or decline.
    - Added **Consistency Scores** to distinguish stable performers from volatile ones.
    - Finalized PDF reporting and feedback logging capabilities.

---

## 🚀 Key Features

### 1. 📊 Intelligent Executive Dashboard
- **Class Health at a Glance**: Donut charts showing distribution of High/Medium/Low performers.
- **Critical Alerts**: "Needs Attention" panel highlighting students with scores < 50%.
- **Consistency Metrics**: Visual volatility indicators (e.g., `±2.5`) to show performance stability.

### 2. 🤖 AI-Driven Analysis Engine
- **Automated Classification**: Logic that considers both current trend and historical average.
- **Smart Recommendations**: Suggests specific remedial courses based on identified weak zones (e.g., Score < 60%).
- **Mentor Matching**: Automatically generates `mentor_pairings.csv` linking struggling students with top performers in the same subject.

### 3. 📈 Student Deep Dive
- **Individual Analyst Reports**: Dedicated view for each student (`/student/<email>`).
- **Trend Graphs**: Line charts visualizing performance trajectory over multiple attempts.
- **Strength/Weakness Profiling**: Auto-generated text summary of a student's capabilities.

### 4. 📝 Feedback & Reporting
- **Centralized Feedback Hub**: Searchable logs of all instructor feedback, filterable by course.
- **PDF Export**: One-click generation of printable student reports.

---

## ✅ Requirement Traceability Matrix (ANAR Compliance)

| ID | Requirement | Status | Feature Implementation |
|---|---|---|---|
| **ANAR1** | **Multi-format Report Reading** | ✅ **Done** | `DataProcessor` handles .csv/.xlsx uploads with dynamic column mapping. |
| **ANAR2** | **Highlight Strength/Weakness** | ✅ **Done** | `PerformanceAnalyzer` tags subjects >80% as Strong, <50% as Weak. |
| **ANAR3** | **Course Recommendations** | ✅ **Done** | `CourseRecommender` maps weak subjects to a 10+ item course catalog. |
| **ANAR4** | **Mentor-Mentee Pairing** | ✅ **Done** | `MentorMatcher` pairs students via Cross-Performance Logic. |
| **ANAR5** | **Improvement Tracking** | ✅ **Done** | Dashboard displays "Improvement Rate" KPIs and Attempt History graphs. |
| **ANAR6** | **Performance Dashboard** | ✅ **Done** | Fully responsive Bootstrap dashboard with real-time Chart.js integration. |
| **ANAR7** | **Web Component Deployment** | ✅ **Done** | Flask Application with Dockerfile and Deployment Guide. |

---

## 💻 Installation & Usage

### Method 1: Python Local (Developers)
1. **Prerequisites**: Python 3.8+
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run Application**:
   ```bash
   python app.py
   ```
4. **Access Dashboard**: Open `http://127.0.0.1:5000`
   - **Login**: `admin@college.edu` / `admin123`

### Method 2: Docker Container (Production)
```bash
docker-compose up --build -d
```
See `DEPLOYMENT.md` for full details.

---

## 📂 Project Structure
```
/AI-Performance-Analyzer
│
├── app.py                 # Core Application Controller (Flask)
├── requirements.txt       # Dependencies
├── ml_engine/             # 🧠 The Brain
│   ├── data_processor.py  # Ingestion & Statistical Analysis (Std Dev, Trends)
│   ├── performance_analyzer.py # Classification Logic
│   ├── recommender.py     # Course Recommendation Engine
│   └── mentor_matcher.py  # Pairing Algorithms
│
├── templates/             # 🎨 The Face
│   ├── dashboard.html     # Main Analytics Hub
│   ├── analysis.html      # Student Detail Report
│   ├── feedback.html      # Feedback Management
│   └── pairing.html       # Mentorship Views
│
└── static/                # Styles & Scripts
```

---

*Project status: **Complete & Verified**. All functional and non-functional requirements have been met.*
