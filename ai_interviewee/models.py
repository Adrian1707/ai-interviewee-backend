from django.db import models
from django.contrib.auth.models import User
from pgvector.django import VectorField
import uuid
from pprint import pprint

class BaseModel(models.Model):
    class Meta:
        abstract = True  # So it doesn't create a table

    @classmethod
    def all(cls):
        return cls.objects.all()

    @classmethod
    def last(cls):
        return cls.objects.last()

    @classmethod
    def get(cls, *args, **kwargs):
        return cls.objects.get(*args, **kwargs)

    def __str__(self):
        # You can customize this as needed
        return f"{pprint(self.__dict__)}"

class UserProfile(BaseModel):
    """Extended user profile for document owners"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    is_searchable = models.BooleanField(default=True)  # Privacy control
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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


class DocumentChunk(BaseModel):
    """Represents a chunk of text extracted from a document with its embedding"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    
    # Content
    content = models.TextField()
    chunk_index = models.PositiveIntegerField()  # Order within the document
    
    # Embedding (using pgvector)
    embedding = VectorField(dimensions=1536, blank=True, null=True)  # Adjust dimensions based on your embedding model
    
    # Metadata
    page_number = models.PositiveIntegerField(null=True, blank=True)
    start_char = models.PositiveIntegerField(null=True, blank=True)
    end_char = models.PositiveIntegerField(null=True, blank=True)
    
    # Extracted metadata (e.g., from PDF structure)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['document', 'chunk_index']
        indexes = [
            models.Index(fields=['document', 'chunk_index']),
        ]
        # Add GIN index for vector similarity search
        # You'll need to create this manually via migration:
        # CREATE INDEX CONCURRENTLY ON myapp_documentchunk USING ivfflat (embedding vector_cosine_ops);