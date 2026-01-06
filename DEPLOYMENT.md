# Deployment Guide for AI-Powered Candidate Performance Analyzer

## Overview
This guide provides instructions for deploying the AI-Powered Candidate Performance Analyzer application in various environments, from local development to production servers.

## Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows
- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Git**: For version control (optional but recommended)

### Hardware Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB+ recommended
- **Storage**: 2GB+ available space

## Deployment Methods

### 1. Local Development Deployment

#### Prerequisites
- Python 3.7 or higher
- pip package manager

#### Steps
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd AI-Powered-Candidate-Performance-Analyzer
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Access the application at `http://localhost:5000`

### 2. Docker Deployment (Recommended)

#### Prerequisites
- Docker Engine
- Docker Compose

#### Steps
1. Ensure all required files are present:
   - `Dockerfile`
   - `docker-compose.yml`
   - `requirements.txt`
   - `app.py`
   - `nginx.conf`

2. Build and run the application:
   ```bash
   docker-compose up --build -d
   ```

3. Access the application at `http://localhost`

4. To view logs:
   ```bash
   docker-compose logs -f
   ```

5. To stop the application:
   ```bash
   docker-compose down
   ```

### 3. Production Deployment

#### Using the provided deployment script

1. Make the deployment script executable:
   ```bash
   chmod +x deploy.sh
   ```

2. Run the deployment script:
   ```bash
   ./deploy.sh
   ```

#### Manual Production Deployment

1. Set up a server with Docker and Docker Compose installed

2. Copy the application files to the server:
   ```bash
   scp -r ./* user@server:/path/to/app
   ```

3. Navigate to the application directory:
   ```bash
   cd /path/to/app
   ```

4. Build and start the application:
   ```bash
   docker-compose up --build -d
   ```

5. Configure a reverse proxy (nginx, Apache) to handle SSL certificates and domain routing

## Configuration Options

### Environment Variables
The application supports the following environment variables:

- `FLASK_ENV`: Set to `production` for production deployment
- `DATABASE_URL`: Database connection string (default: SQLite file)

### Port Configuration
- The application runs on port 8000 inside the container
- The nginx proxy exposes the application on port 80
- To change ports, modify the `docker-compose.yml` file

## Scaling and Performance

### Worker Configuration
The Gunicorn configuration is set to use 4 worker processes by default. For higher traffic applications, adjust the `workers` value in `gunicorn.conf.py`:

```python
workers = min(2 * (number_of_cpu_cores) + 1, 8)
```

### Database Considerations
- The application uses SQLite by default, which is suitable for small to medium deployments
- For high-traffic applications, consider migrating to PostgreSQL or MySQL
- Regular database backups should be scheduled

## Security Considerations

### HTTPS/SSL
For production deployments, configure SSL certificates:
1. Update nginx.conf to include SSL configuration
2. Obtain SSL certificates (Let's Encrypt, commercial certificates)
3. Configure automatic certificate renewal

### Access Control
- Implement authentication for sensitive endpoints
- Use environment variables for sensitive configuration
- Regular security updates for base images

### File Upload Security
- Validate file types and sizes
- Scan uploaded files for malware
- Store files in secure locations

## Monitoring and Logging

### Application Logs
Logs are accessible via:
```bash
docker-compose logs -f web
```

### Health Checks
The application includes health check endpoints:
- `/health` - Basic health check
- Application logs contain detailed request/response information

### Performance Monitoring
Monitor the following metrics:
- Response times
- Error rates
- Resource utilization
- Database connection pool usage

## Backup and Recovery

### Database Backup
Regular backups of the SQLite database should be scheduled:
```bash
cp performance_analyzer.db performance_analyzer_$(date +%Y%m%d_%H%M%S).db
```

### Configuration Backup
Backup the following files:
- `docker-compose.yml`
- `nginx.conf`
- `gunicorn.conf.py`
- `requirements.txt`

## Troubleshooting

### Common Issues

#### Application won't start
1. Check Docker logs:
   ```bash
   docker-compose logs web
   ```
2. Verify all required files are present
3. Check file permissions

#### Database connection issues
1. Verify database file permissions
2. Check database file path in configuration
3. Ensure database is not corrupted

#### Performance issues
1. Check system resources (CPU, memory)
2. Review Gunicorn worker configuration
3. Optimize database queries if needed

### Debugging
For debugging in production, temporarily enable debug mode:
```bash
docker-compose exec web bash
```

## Updates and Maintenance

### Applying Updates
1. Backup current deployment
2. Pull latest code changes
3. Rebuild Docker images:
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Rolling Updates
For zero-downtime deployments, consider using a load balancer with multiple application instances.

## Architecture Overview

```
Internet
    ↓
Nginx (Port 80)
    ↓
Gunicorn (Port 8000)
    ↓
Flask Application
    ↓
SQLite Database
```

## Support and Maintenance

### Support Channels
- GitHub Issues for bug reports
- Documentation for configuration help
- Community forums for general questions

### Maintenance Schedule
- Regular security updates
- Monthly performance reviews
- Quarterly architecture reviews

## Additional Resources

- [README.md](README.md) - Main project documentation
- [Database Schema](docs/DATABASE_SCHEMA.md) - Database structure details
- [ML Algorithms](docs/ML_ALGORITHMS.md) - Machine learning implementation details
- [API Documentation](docs/API.md) - API endpoints and usage