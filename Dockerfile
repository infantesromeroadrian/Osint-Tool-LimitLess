FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    cmake \
    git \
    curl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip with retry mechanism
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip config set global.retries 10

# Copy requirements first for better caching
COPY requirements.txt .

# Install basic dependencies first
RUN pip install --no-cache-dir numpy pandas

# Install PyTorch with specific version (smaller) and retry mechanism
RUN pip install --no-cache-dir torch==1.13.1+cpu --extra-index-url https://download.pytorch.org/whl/cpu

# Install OpenAI dependency (using older version that doesn't have proxy issues)
RUN pip install --no-cache-dir openai==0.28.1

# Install huggingface and transformers dependencies
RUN pip install --no-cache-dir huggingface-hub==0.16.4 transformers==4.30.2 sentence-transformers==2.2.2

# Install remaining requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy the model download script and run it (will be replaced when we copy the full app)
COPY download_model.py .
RUN mkdir -p /root/.cache/torch/sentence_transformers/
RUN python download_model.py || echo "Model download failed, will use fallback mode"

# Make data directories
RUN mkdir -p data/chroma_db data/documents data/casos data/image_analysis data/transcriptions

# Create directory for NLTK data
RUN mkdir -p /app/nltk_data && chmod 777 /app/nltk_data

# Download NLTK data as root (before switching to app user)
ENV NLTK_DATA=/app/nltk_data
RUN python -c "import nltk; nltk.download('punkt', download_dir='/app/nltk_data')"

# Install spaCy language model
RUN python -m spacy download en_core_web_sm

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
ENV NLTK_DATA=/app/nltk_data
ENV SENTENCE_TRANSFORMERS_HOME=/home/app/.cache/torch/sentence_transformers

# Expose Streamlit port
EXPOSE 8501

# Command to run the application, fixing permissions first
CMD ["sh", "-c", "/app/fix-permissions.sh && streamlit run src/main.py --server.address=0.0.0.0"] 