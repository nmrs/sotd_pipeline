FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy pipeline code
COPY sotd/ ./sotd/
COPY run.py .

# Create scripts directory and copy search index generator
RUN mkdir -p ./scripts
COPY scripts/generate_search_index.py ./scripts/generate_search_index.py

# Copy container scripts
COPY docker/pipeline/run-pipeline.sh ./run-pipeline.sh
COPY docker/pipeline/entrypoint.sh ./entrypoint.sh

# Make scripts executable
RUN chmod +x ./run-pipeline.sh ./entrypoint.sh

# Create data directory (will be mounted as volume)
RUN mkdir -p /data

# Set environment variables
ENV SOTD_DATA_DIR=/data
ENV PYTHONUNBUFFERED=1

# Entry point
ENTRYPOINT ["./entrypoint.sh"]
