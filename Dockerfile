FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and templates
COPY src/ /app/src/
COPY templates/ /app/templates/

# Ensure data directory exists
RUN mkdir -p /app/data

# PYTHONPATH needs to include src
ENV PYTHONPATH=/app/src

EXPOSE 8000

# Run the FastAPI app via uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
