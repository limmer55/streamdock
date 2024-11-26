# Base image
FROM python:3.11-slim

# Set environment variables für non-free Repositorys und VAAPI
ENV DEBIAN_FRONTEND=noninteractive
ENV LIBVA_DRIVER_NAME=iHD
ENV XDG_RUNTIME_DIR=/tmp

# Enable non-free and contrib repositories
RUN sed -i 's/main/main contrib non-free/' /etc/apt/sources.list

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required for the application, ffmpeg, VAAPI, and firmware
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    libva-dev \
    libdrm-dev \
    vainfo \
    libmfx-dev \
    intel-media-va-driver-non-free \
    firmware-misc-nonfree \
    libva-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 6050

# Command to start the application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:6050", "run:app", "--workers", "$(expr $(nproc) * 2 + 1)"]
