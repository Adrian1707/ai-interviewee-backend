import pytest
import os
import django
from django.conf import settings
from django.test.utils import get_runner


def pytest_configure():
    """Configure Django settings for pytest."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_interviewee.test_settings')
    django.setup()


@pytest.fixture(scope="session")
def django_db_setup():
    """Set up the test database configuration."""
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.environ.get("DB_HOST", "db"),
        "NAME": os.environ.get("DB_NAME", "test_mydb"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "mypassword"),
        "USER": os.environ.get("DB_USER", "myuser"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        'ATOMIC_REQUESTS': False,
    }
