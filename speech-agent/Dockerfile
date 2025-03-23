FROM python:3.9-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m appuser
USER appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py /app/app.py
COPY index.html /app/index.html
COPY gunicorn_config.py /app/gunicorn_config.py

# Create cache directory
RUN mkdir -p /app/cache

# Expose port
EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8000/ || exit 1

# Start the application with Gunicorn
CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]
