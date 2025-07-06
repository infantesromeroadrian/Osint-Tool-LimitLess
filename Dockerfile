FROM python:3.9-slim

WORKDIR /app

# Install system dependencies including FFmpeg for video/audio metadata
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    cmake \
    git \
    curl \
    ca-certificates \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip with retry mechanism
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip config set global.retries 10

# Copy requirements first for better caching
COPY requirements.txt .

# Install Flask application requirements (includes spaCy model from URL)
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data with simple commands
RUN python -c "import nltk; nltk.download('punkt', quiet=True)" || echo "Failed to download punkt"
RUN python -c "import nltk; nltk.download('stopwords', quiet=True)" || echo "Failed to download stopwords"
RUN python -c "import nltk; nltk.download('wordnet', quiet=True)" || echo "Failed to download wordnet"
RUN python -c "import nltk; nltk.download('omw-1.4', quiet=True)" || echo "Failed to download omw-1.4"
RUN python -c "import nltk; nltk.download('vader_lexicon', quiet=True)" || echo "Failed to download vader_lexicon"

# Create cache directories for future model downloads
RUN mkdir -p /root/.cache/torch/sentence_transformers/

# Make data directories
RUN mkdir -p data/chroma_db data/documents data/casos data/image_analysis data/transcriptions

# Create app directories
RUN mkdir -p /app/logs

# Copy the rest of the application
COPY . .

# Create a non-root user with proper home directory
RUN addgroup --system app && \
    adduser --system --ingroup app --home /app --no-create-home app

# Fix permissions for data directories - ensure full write access for mounted volumes
RUN mkdir -p /app/data/casos /app/data/documents /app/data/chroma_db /app/data/transcriptions /app/data/image_analysis && \
    chmod -R 777 /app/data && \
    find /app/data -type d -exec chmod 777 {} \; && \
    chown -R app:app /app && \
    # Make the app directory world-writable for volume mounts
    chmod -R 777 /app/data

# Ensure model cache is accessible to app user
RUN mkdir -p /home/app/.cache && \
    cp -r /root/.cache/torch /home/app/.cache/ || true && \
    chown -R app:app /home/app/.cache

# Copy NLTK data to app user directory
RUN mkdir -p /home/app/nltk_data && \
    cp -r /root/nltk_data/* /home/app/nltk_data/ 2>/dev/null || true && \
    chown -R app:app /home/app/nltk_data || true

# Set NLTK data path for app user
ENV NLTK_DATA=/home/app/nltk_data

# Create script to fix permissions on startup
RUN echo '#!/bin/sh' > /app/fix-permissions.sh && \
    echo '# Fix permissions for mounted volumes on container startup' >> /app/fix-permissions.sh && \
    echo 'find /app/data -type d -exec chmod 777 {} \;' >> /app/fix-permissions.sh && \
    echo 'find /app/data -type f -exec chmod 666 {} \;' >> /app/fix-permissions.sh && \
    chmod +x /app/fix-permissions.sh

# Switch to non-root user
USER app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=src/app.py

# Expose Flask port
EXPOSE 5000

# Command to run the application, fixing permissions first
CMD ["sh", "-c", "/app/fix-permissions.sh && python src/app.py"] 