# Start from a Python base image
FROM python:3.11-slim

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


# ARG PYTHON_VERSION=3.13-slim

# FROM python:${PYTHON_VERSION}

# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1

# RUN mkdir -p /code

# WORKDIR /code

# COPY requirements.txt /tmp/requirements.txt
# RUN set -ex && \
#     pip install --upgrade pip && \
#     pip install -r /tmp/requirements.txt && \
#     rm -rf /root/.cache/
# COPY . /code

# EXPOSE 8000

# CMD ["gunicorn","--bind",":8000","--workers","2","ai_interviewee.wsgi"]
