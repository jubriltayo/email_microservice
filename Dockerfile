FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files (will run in docker-compose)
# RUN python manage.py collectstatic --noinput

# Create non-root user (optional but recommended)
RUN useradd --create-home --shell /bin/bash app
USER app

# Expose port
EXPOSE 8001

# Default command (overridden in docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]