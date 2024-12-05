# Base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Add required repositories and update package lists
RUN echo 'deb http://deb.debian.org/debian bookworm main contrib non-free non-free-firmware' > /etc/apt/sources.list.d/debian-testing.list && \
    apt-get update && apt-get install -y --no-install-recommends \
    apt-transport-https \
    gnupg \
    wget \
    lbzip2 \
    procps \
    unzip \
    locales \
    tzdata \
    libxml2 \
    xz-utils \
    curl \
    lsof \
    jq \
    nethogs \
    intel-media-va-driver-non-free \
    i965-va-driver \
    mesa-va-drivers \
    vainfo \
    ffmpeg \
    build-essential \
    libvulkan1 \
    mesa-vulkan-drivers && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into the container
COPY . .

# Set environment variables for Flask
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Expose the port the app runs on
EXPOSE 6050

# Command to start the application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:6050", "run:app", "--workers", "4"]
