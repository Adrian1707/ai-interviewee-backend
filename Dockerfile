# Start from a Python base image
FROM python:3.11-slim

# Install PostgreSQL client for psql command
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Install requirements early (for cache)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of your project
COPY . .

# Expose port 8000 (optional, but recommended for clarity)
EXPOSE 8080

# Run Django's development server accessible externally
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
