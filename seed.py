import sys
import os
import django

# Add project root to Python path (so it can find 'ai_interviewee')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the DJANGO_SETTINGS_MODULE
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_interviewee.settings")

# Initialize Django
django.setup()

from django.contrib.auth.models import User
from ai_interviewee.models import UserProfile 



def create_user_profile():
    # Create a user (if not exists)
    username = "testuser"
    email = "testuser@example.com"
    password = "testpassword"

    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        print(f"Created user: {username}")
    else:
        print(f"User '{username}' already exists.")

    # Create or update the profile
    user = User.objects.get(username=username)
    profile, created = UserProfile.objects.get_or_create(user=user)

    if created:
        print("Created new user profile.")
        profile.display_name = "Test User"
        profile.bio = "This is a test bio for the user profile."
        profile.is_searchable = True
        profile.save()
    else:
        print("User profile already exists.")

if __name__ == "__main__":
    create_user_profile()