from celery import shared_task
from django.utils import timezone
from django.core.files.storage import default_storage
from ai_interviewee.models import Document, DocumentChunk
from .utils import extract_text_from_file, chunk_text
from .services import OpenAIEmbeddingService
import logging
import traceback

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_document_task(self, document_id):
    """
    Main task to process an uploaded document
    """
    try:
        # Get the document
        document = Document.objects.get(id=document_id)
        
        # Update status to processing
        document.processing_status = 'processing'
        document.save()
        
        logger.info(f"Starting processing for document {document_id}")
        
        # Extract text from the document
        text_content = extract_text_from_file(document.file.path)
        
        if not text_content:
            raise Exception("No text content could be extracted from the document")
        
        # Chunk the text
        chunks = chunk_text(text_content)
        
        logger.info(f"Created {len(chunks)} chunks for document {document_id}")
        
        # Create DocumentChunk objects and trigger embedding generation
        for i, chunk_data in enumerate(chunks):
            chunk = DocumentChunk.objects.create(
                document=document,
                content=chunk_data['content'],
                chunk_index=i,
                page_number=chunk_data.get('page_number'),
                start_char=chunk_data.get('start_char'),
                end_char=chunk_data.get('end_char'),
                metadata=chunk_data.get('metadata', {})
            )
            
            # Queue embedding generation (placeholder for now)
            generate_embedding_task.delay(chunk.id)
        
        # Update document status
        document.processing_status = 'completed'
        document.processed_at = timezone.now()
        document.save()
        
        logger.info(f"Successfully processed document {document_id}")
        
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        raise
    
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Update document with error status
        # The 'document' object should be defined here unless Document.DoesNotExist was raised,
        # which is caught separately.
        if 'document' in locals() and document: # Ensure document object exists
            document.processing_status = 'failed'
            document.processing_error = str(e)
            document.save()
        
        # Retry the task
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def generate_embedding_task(self, chunk_id):
    """
    Placeholder task for generating embeddings
    This is where you'll add your embedding logic later
    """
    try:
        chunk = DocumentChunk.objects.get(id=chunk_id)
        logger.info(f"Generating embedding for chunk {chunk_id}")
        
        # Initialize the embedding service
        embedding_service = OpenAIEmbeddingService()
        
        # Generate the embedding
        embedding = embedding_service.generate_embedding(chunk.content)
        
        if embedding:
            chunk.embedding = embedding
            chunk.save()
            logger.info(f"Successfully generated and saved embedding for chunk {chunk_id}")
            return f"Embedding generated for chunk {chunk_id}"
        else:
            raise Exception("Embedding generation returned no data.")
        
    except DocumentChunk.DoesNotExist:
        logger.error(f"DocumentChunk {chunk_id} not found")
        raise
    
    except Exception as e:
        logger.error(f"Error generating embedding for chunk {chunk_id}: {str(e)}")
        # Retry the task
        raise self.retry(exc=e, countdown=30)
