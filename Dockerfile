# Multi-stage build for SAM.gov Opportunity Analysis System

# Stage 1: Python Backend
FROM python:3.11-slim as backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Additional requirements for new features
RUN pip install --no-cache-dir \
    schedule==1.2.0 \
    neo4j==5.14.0 \
    requests==2.31.0

# Copy backend code
COPY *.py ./
COPY client/ ./client/
COPY config.yaml .
COPY config_db.py .

# Stage 2: Node.js Frontend Builder
FROM node:18-alpine as frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./
RUN npm ci --only=production

# Copy frontend source
COPY frontend/ .

# Build frontend
RUN npm run build

# Stage 3: Final Runtime Image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python environment from backend stage
COPY --from=backend /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=backend /app /app

# Copy built frontend
COPY --from=frontend-builder /app/frontend/build /app/frontend/build

# Copy nginx configuration
COPY docker/nginx.conf /etc/nginx/sites-available/default

# Copy supervisor configuration
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create necessary directories
RUN mkdir -p /var/log/supervisor

# Expose ports
EXPOSE 80 5001

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]