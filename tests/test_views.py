import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from ai_interviewee.models import Document

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_document_upload_success(api_client):
    url = reverse('document-upload')
    file_content = b"This is a test document content."
    uploaded_file = SimpleUploadedFile("test_document.txt", file_content, content_type="text/plain")
    
    # Create a test user (required by your serializer)
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username='testuser', password='testpass')
    api_client.force_authenticate(user=user)
    
    # Use valid document_type choice and JSON tags
    data = {
        'file': uploaded_file,
        'title': 'Test Document',
        'is_public': True,
        'tags': '["test", "document"]'  # JSON-formatted string
    }

    with patch('ai_interviewee.tasks.process_document_task.delay') as mock_delay:
        response = api_client.post(url, data, format='multipart')
        
        # Debugging: Print errors if any
        if response.status_code != 201:
            print("Response errors:", response.data)
            
        assert response.status_code == 201
        assert 'message' in response.data
        assert 'document' in response.data
        assert response.data['message'] == 'Document uploaded successfully and queued for processing'
        
        # Verify that the document was saved to the database
        document = Document.objects.get(id=response.data['document']['id'])

        assert "test_document" in document.file.name

        assert document.processing_status == 'pending'
        
        # Verify that the Celery task was called
        mock_delay.assert_called_once_with(document.id)

# @pytest.mark.django_db
# def test_document_upload_no_file(api_client):
#     url = reverse('document-upload')
#     response = api_client.post(url, {}, format='multipart')
#     assert response.status_code == 400
#     assert 'file' in response.data

# @pytest.mark.django_db
# def test_document_upload_invalid_file_type(api_client):
#     url = reverse('document-upload')
#     # Create a dummy file with an invalid content type
#     file_content = b"This is an invalid file type."
#     uploaded_file = SimpleUploadedFile("test_document.exe", file_content, content_type="application/x-msdownload")

#     response = api_client.post(url, {'file': uploaded_file}, format='multipart')
#     assert response.status_code == 400
#     assert 'file' in response.data

# # To test the full stack, we need to mock the OpenAI API call within the process_document_task.
# # This requires knowing where the OpenAI call is made.
# # Let's assume for now it's in ai_interviewee.embedding_service.OpenAIEmbeddingService.get_embedding
# # We will refine this mock if needed after inspecting embedding_service.py and services.py

# @pytest.mark.django_db
# def test_full_stack_document_processing(api_client):
#     url = reverse('document-upload')
#     file_content = b"This is a test document content for full stack processing."
#     uploaded_file = SimpleUploadedFile("full_stack_test.txt", file_content, content_type="text/plain")

#     # Mock the OpenAI API call
#     with patch('ai_interviewee.embedding_service.OpenAIEmbeddingService.generate_embedding') as mock_generate_embedding:
#         mock_generate_embedding.return_value = [0.1, 0.2, 0.3] # Dummy embedding

#         # Mock process_document_task.delay to run synchronously
#         with patch('ai_interviewee.tasks.process_document_task.delay', side_effect=lambda doc_id: process_document_task(doc_id)) as mock_process_delay:
#             # Mock generate_embedding_task.delay to run synchronously within process_document_task
#             with patch('ai_interviewee.tasks.generate_embedding_task.delay', side_effect=lambda chunk_id: generate_embedding_task(chunk_id)) as mock_generate_delay:
#                 from ai_interviewee.tasks import process_document_task, generate_embedding_task # Import tasks here to ensure patched versions are used

#                 response = api_client.post(url, {'file': uploaded_file}, format='multipart')

#                 assert response.status_code == 201
#                 document_id = response.data['document']['id']
                
#                 # After the task runs synchronously, check the document status and chunks
#                 document = Document.objects.get(id=document_id)
#                 assert document.processing_status == 'completed' # Check for 'completed' status
#                 assert document.documentchunk_set.count() > 0 # Assuming chunks are created

#                 mock_generate_embedding.assert_called() # Verify that generate_embedding was called
#                 mock_process_delay.assert_called_once() # Verify process_document_task.delay was called
#                 mock_generate_delay.assert_called() # Verify generate_embedding_task.delay was called for each chunk
