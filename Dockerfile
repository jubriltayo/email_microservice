FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Expose port (Railway uses dynamic PORT, so this is only informative)
EXPOSE 8000

# Run migrations, collectstatic, then start gunicorn
CMD sh -c "python manage.py migrate && \
           python manage.py collectstatic --noinput && \
           gunicorn core.wsgi:application --bind 0.0.0.0:$PORT"
