FROM python:3.11-slim

# Install system dependencies (poppler-utils is required by pdf2image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Default port
ENV PORT=8000
EXPOSE 8000

# Start command using dynamic PORT
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
