from django.db import models
from django.contrib.auth.models import User

class Persona(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    headline = models.CharField(max_length=255)
    summary = models.TextField()

    def __str__(self):
        return self.name

class InterviewSession(models.Model):
    interviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interview_sessions')
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    # Add other fields relevant to an interview session, e.g., start_time, end_time, status
    # For now, keeping it minimal as per request

    def __str__(self):
        return f"Session with {self.persona.name} by {self.interviewer.username}"

class ChatMessage(models.Model):
    SENDER_ROLES = (
        ('user', 'User'),
        ('ai', 'AI'),
    )
    interview_session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE)
    content = models.TextField()
    sender_role = models.CharField(max_length=10, choices=SENDER_ROLES)
    context_debug = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender_role}: {self.content[:50]}..."
