# Database Schema Documentation

## Overview
The AI-Powered Candidate Performance Analyzer uses SQLite for data persistence. The database contains several tables to store student information, course data, scores, recommendations, mentor pairings, and progress tracking information.

## Tables

### 1. students
Stores information about students in the system.

**Columns:**
- `id`: INTEGER PRIMARY KEY - Auto-incrementing primary key
- `student_id`: TEXT UNIQUE NOT NULL - Unique identifier for the student
- `name`: TEXT NOT NULL - Student's full name
- `email`: TEXT UNIQUE NOT NULL - Student's email address
- `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP - When the record was created

**Sample Data:**
```
id | student_id | name          | email
1  | S001       | John Doe      | john@example.com
2  | S002       | Jane Smith    | jane@example.com
```

### 2. courses
Stores information about available courses.

**Columns:**
- `id`: INTEGER PRIMARY KEY - Auto-incrementing primary key
- `course_id`: TEXT UNIQUE NOT NULL - Unique identifier for the course
- `course_name`: TEXT NOT NULL - Name of the course
- `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP - When the record was created

**Sample Data:**
```
id | course_id | course_name
1  | C001      | Mathematics
2  | C002      | Physics
```

### 3. scores
Stores student performance scores for each course attempt.

**Columns:**
- `id`: INTEGER PRIMARY KEY - Auto-incrementing primary key
- `student_id`: TEXT NOT NULL - References students table
- `course_id`: TEXT NOT NULL - References courses table
- `attempt_id`: INTEGER - Attempt number for the course
- `attempt_timestamp`: TIMESTAMP - When the attempt was made
- `score`: REAL - Score achieved
- `max_score`: REAL - Maximum possible score
- `grade`: TEXT - Letter grade (A, B, C, etc.)
- `topic_tags`: TEXT - Topic tags related to the attempt
- `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP - When the record was created

**Sample Data:**
```
id | student_id | course_id | attempt_id | score | max_score | grade
1  | S001       | C001      | 1          | 85    | 100       | A
2  | S001       | C002      | 1          | 45    | 100       | F
```

### 4. recommendations
Stores course recommendations for students.

**Columns:**
- `id`: INTEGER PRIMARY KEY - Auto-incrementing primary key
- `student_id`: TEXT NOT NULL - References students table
- `course_id`: TEXT NOT NULL - References courses table
- `recommendation`: TEXT - Recommendation text
- `priority`: TEXT - Priority level (High, Medium, Low)
- `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP - When the record was created

**Sample Data:**
```
id | student_id | course_id | recommendation          | priority
1  | S001       | C002      | Review fundamental topics | High
2  | S002       | C001      | Practice advanced problems | Medium
```

### 5. pairings
Stores mentor-mentee pairings.

**Columns:**
- `id`: INTEGER PRIMARY KEY - Auto-incrementing primary key
- `course_id`: TEXT NOT NULL - References courses table
- `weak_student_id`: TEXT NOT NULL - References students table (mentee)
- `mentor_id`: TEXT NOT NULL - References students table (mentor)
- `compatibility_score`: REAL - Score representing compatibility
- `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP - When the record was created

**Sample Data:**
```
id | course_id | weak_student_id | mentor_id | compatibility_score
1  | C001      | S002           | S001      | 85.5
2  | C002      | S003           | S001      | 92.0
```

### 6. course_completions
Tracks course completion status for students.

**Columns:**
- `id`: INTEGER PRIMARY KEY - Auto-incrementing primary key
- `student_id`: TEXT NOT NULL - References students table
- `course_id`: TEXT NOT NULL - References courses table
- `completion_date`: TIMESTAMP - When the course was completed
- `completion_status`: TEXT DEFAULT 'in_progress' - Status (in_progress, completed, abandoned)
- `completion_percentage`: REAL DEFAULT 0 - Completion percentage
- `estimated_completion_time`: TEXT - Estimated time to completion
- `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP - When the record was created

**Sample Data:**
```
id | student_id | course_id | completion_status | completion_percentage
1  | S001       | C001      | completed         | 100
2  | S002       | C002      | in_progress       | 75
```

### 7. improvement_tracking
Tracks improvement metrics for students.

**Columns:**
- `id`: INTEGER PRIMARY KEY - Auto-incrementing primary key
- `student_id`: TEXT NOT NULL - References students table
- `course_id`: TEXT NOT NULL - References courses table
- `initial_score`: REAL - Initial score before improvement
- `final_score`: REAL - Final score after improvement
- `improvement_percentage`: REAL - Percentage improvement
- `completion_date`: TIMESTAMP - When improvement was measured
- `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP - When the record was created

**Sample Data:**
```
id | student_id | course_id | initial_score | final_score | improvement_percentage
1  | S001       | C001      | 60            | 85          | 41.67
2  | S002       | C002      | 40            | 70          | 75.00
```

## Relationships

- `scores.student_id` → `students.student_id`
- `scores.course_id` → `courses.course_id`
- `recommendations.student_id` → `students.student_id`
- `recommendations.course_id` → `courses.course_id`
- `pairings.weak_student_id` → `students.student_id`
- `pairings.mentor_id` → `students.student_id`
- `pairings.course_id` → `courses.course_id`
- `course_completions.student_id` → `students.student_id`
- `course_completions.course_id` → `courses.course_id`
- `improvement_tracking.student_id` → `students.student_id`
- `improvement_tracking.course_id` → `courses.course_id`

## Indexes

The database automatically creates indexes on primary keys and unique constraints. Additional indexes can be added for performance optimization based on query patterns.