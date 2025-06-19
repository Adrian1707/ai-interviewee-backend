from django.db import models
from pgvector.django import VectorField
import uuid
from .base_model import BaseModel
from .document import Document

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
