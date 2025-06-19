from django.db import models
from django.contrib.auth.models import User
import uuid
from .base_model import BaseModel

class Document(BaseModel):
    """Represents an uploaded document"""
    DOCUMENT_TYPES = [
        ('cv', 'CV/Resume'),
        ('portfolio', 'Portfolio'),
        ('cover_letter', 'Cover Letter'),
        ('transcript', 'Transcript'),
        ('certificate', 'Certificate'),
        ('project_explanation', 'Project Explanation'),
        ('other', 'Other'),
    ]

    DOCUMENT_TYPE_CHOICES = [
        ('PDF', 'PDF'),
        ('TXT', 'Text File'),
        ('DOC', 'Word Document'),
        ('DOCX', 'Word Document (DOCX)'),
    ]
    
    PROCESSING_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='other')
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    file_size = models.PositiveIntegerField(null=True, blank=True)  # in bytes
    mime_type = models.CharField(max_length=100, blank=True)
    
    # Processing status
    processing_status = models.CharField(max_length=20, choices=PROCESSING_STATUS, default='pending')
    processing_error = models.TextField(blank=True, null=True)
    
    # Metadata
    is_public = models.BooleanField(default=True)  # Whether others can search this document
    tags = models.JSONField(default=list, blank=True)  # User-defined tags
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['owner', 'processing_status']),
            models.Index(fields=['document_type', 'is_public']),
        ]
