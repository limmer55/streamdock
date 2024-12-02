# Base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required for the application and ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into the container
COPY . .

# Set environment variables for Flask
ENV FLASK_APP run.py
ENV FLASK_ENV production

# Expose the port the app runs on
EXPOSE 6050

# Command to start the application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:6050", "run:app"]
