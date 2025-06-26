from django.db import models
from .base_model import BaseModel

class Skill(BaseModel):
    """Skill"""
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
