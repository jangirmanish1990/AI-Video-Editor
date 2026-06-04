FROM python:3.12-slim

# Install FFmpeg (required for all edit ops)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure writable dirs exist
RUN mkdir -p uploads logs

ENV PYTHONUNBUFFERED=1

# Render injects $PORT; default to 8000 for local testing
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
