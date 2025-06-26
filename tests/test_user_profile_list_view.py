import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from ai_interviewee.models import UserProfile, Skill
from django.contrib.auth.models import User
from datetime import date

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_user_profile_list_view(api_client):
    url = reverse('user-profile-list')
    user1 = User.objects.create_user(username='testuser1', password='testpassword')
    user2 = User.objects.create_user(username='testuser2', password='testpassword')
    skill1 = Skill.objects.create(name='Python')
    skill2 = Skill.objects.create(name='Django')
    profile1 = UserProfile.objects.create(
        user=user1,
        display_name='Test User 1',
        bio='Test Bio 1',
        career_start_date=date(2020, 1, 1),
        is_searchable=True
    )
    profile1.skills.add(skill1)
    profile2 = UserProfile.objects.create(
        user=user2,
        display_name='Test User 2',
        bio='Test Bio 2',
        career_start_date=date(2022, 1, 1),
        is_searchable=False
    )
    profile2.skills.add(skill2)

    response = api_client.get(url)

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['display_name'] == 'Test User 1'
    assert response.data[0]['bio'] == 'Test Bio 1'
    assert response.data[0]['years_of_experience'] == date.today().year - 2020
    assert response.data[0]['skills'] == ['Python']
