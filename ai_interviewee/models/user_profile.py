from django.db import models
from django.contrib.auth.models import User
from .base_model import BaseModel
from .skill import Skill

class UserProfile(BaseModel):
    """Extended user profile for document owners"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    skills = models.ManyToManyField(Skill, through='UserProfileSkill')
    display_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    career_start_date = models.DateField(null=True)
    is_searchable = models.BooleanField(default=True)  # Privacy control
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
