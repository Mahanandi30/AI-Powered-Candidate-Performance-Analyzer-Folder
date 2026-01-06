# Deployment Guide

This document outlines how to deploy the **AI-Powered Candidate Performance Analyzer** locally and via Docker.

## 🏗️ Prerequisites
- **Python 3.7+** (For local run)
- **Docker** and **Docker Compose** (For containerized run)
- Git (Optional)

---

## 💻 Local Deployment (Quick Start)

1.  **Environment Setup**:
    It is recommended to use a virtual environment.
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Initialize Database**:
    The application automatically initializes `performance.db` on first run. No manual setup required for SQLite.

4.  **Run Application**:
    ```bash
    python app.py
    ```

5.  **Access**:
    Navigate to `http://localhost:5000`.

---

## 🐳 Docker Deployment

The application is container-ready. This ensures consistency across different environments.

### 1. Build the Image
Navigate to the project root and run:
```bash
docker build -t cpa-tool:latest .
```

### 2. Run Container
```bash
docker run -d -p 5000:5000 --name cpa-instance cpa-tool:latest
```

### 3. Using Docker Compose (Recommended)
If you need to scale or add a dedicated database service (like PostgreSQL) later, use Compose.

**File:** `docker-compose.yml`
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - .:/app
    environment:
      - FLASK_ENV=development
```

**Command to run:**
```bash
docker-compose up --build -d
```

---

## ☁️ Cloud Deployment Guidelines

### Heroku
1.  Create a `Procfile` in root: `web: gunicorn app:app`
2.  Install `gunicorn`: `pip install gunicorn` (Add to requirements.txt)
3.  Push to Heroku Git.

### AWS (EC2)
1.  Launch an Ubuntu EC2 instance.
2.  Install Docker.
3.  Clone the repo.
4.  Run `docker-compose up`.

---

## 🔧 Troubleshooting

-   **Port Conflicts**: If port 5000 is busy, change the port in `app.py` or the Docker mapping (`-p 8080:5000`).
-   **Database Locks**: If using SQLite locally, ensure no other process is holding the file lock.
-   **Missing Modules**: Ensure you ran `pip install` inside the correct environment.
