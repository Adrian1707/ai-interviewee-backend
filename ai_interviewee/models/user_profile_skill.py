from django.db import models
from .base_model import BaseModel
from .skill import Skill
from .user_profile import UserProfile

class UserProfileSkill(BaseModel):
    """Skill for a UserProfile"""
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
