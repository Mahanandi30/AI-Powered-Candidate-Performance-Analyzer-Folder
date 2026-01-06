#!/bin/bash

# Deployment script for AI-Powered Candidate Performance Analyzer

set -e  # Exit on any error

echo "Starting deployment of AI-Powered Candidate Performance Analyzer..."

# Check if Docker is installed
if ! [ -x "$(command -v docker)" ]; then
  echo "Error: Docker is not installed." >&2
  exit 1
fi

# Check if docker-compose is installed
if ! [ -x "$(command -v docker-compose)" ]; then
  echo "Error: docker-compose is not installed." >&2
  exit 1
fi

echo "Building and starting the application..."

# Build and start the services
docker-compose up --build -d

echo "Waiting for the application to start..."
sleep 30

# Check if the application is running
if docker-compose ps | grep -q "Up"; then
    echo "Application is running successfully!"
    echo "Access the application at http://localhost"
else
    echo "There might be an issue with the application startup."
    docker-compose logs
    exit 1
fi

echo "Deployment completed successfully!"
echo "Application is available at http://localhost"
echo "To view logs: docker-compose logs -f"
echo "To stop the application: docker-compose down"