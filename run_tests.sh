#!/bin/bash
set -e

# Create test database if it doesn't exist
python -c "
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

conn = psycopg2.connect(
    host='db',
    database='postgres',
    user='myuser',
    password='mypassword'
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

try:
    cur.execute('CREATE DATABASE test_mydb;')
    print('Test database created')
except psycopg2.errors.DuplicateDatabase:
    print('Test database already exists')

cur.close()
conn.close()
"

# Connect to test database and create vector extension
python -c "
import psycopg2

conn = psycopg2.connect(
    host='db',
    database='test_mydb',
    user='myuser',
    password='mypassword'
)
cur = conn.cursor()
cur.execute('CREATE EXTENSION IF NOT EXISTS vector;')
conn.commit()
cur.close()
conn.close()
print('Vector extension created')
"

# Set Django settings module for tests
export DJANGO_SETTINGS_MODULE=ai_interviewee.test_settings

# Run migrations and tests
export DATABASE_URL=postgres://myuser:mypassword@db:5432/test_mydb
export DB_NAME=test_mydb
export DB_HOST=db
export DB_USER=myuser
export DB_PASSWORD=mypassword
export DB_PORT=5432

# Run migrations on test database
python manage.py migrate --settings=ai_interviewee.test_settings

# Run tests with proper Django configuration
pytest --ds=ai_interviewee.test_settings -v
