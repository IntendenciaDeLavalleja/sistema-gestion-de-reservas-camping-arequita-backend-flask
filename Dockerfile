FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc_dir

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libmariadb-dev \
    pkg-config \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . .

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 5000

# Run entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]