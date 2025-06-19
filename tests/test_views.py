import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from ai_interviewee.models import Document, UserProfile

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

from ai_interviewee.models import UserProfile

@pytest.mark.django_db
@pytest.mark.usefixtures('setup') # Apply the setup fixture to all tests in this class
class TestRagQueryView:
    @pytest.fixture() # Removed autouse=True
    def setup(self, api_client):
        self.client = api_client

        # Patch OpenAIEmbeddingService.generate_embedding
        self.embedding_patcher = patch('ai_interviewee.services.rag_service.OpenAIEmbeddingService.generate_embedding')
        self.mock_generate_embedding = self.embedding_patcher.start()
        self.mock_generate_embedding.return_value = [0.1] * 1536  # Dummy embedding

        # Patch openai.OpenAI client's chat completions create method
        self.openai_patcher = patch('openai.OpenAI')
        self.mock_openai_client_class = self.openai_patcher.start()
        self.mock_openai_client_instance = self.mock_openai_client_class.return_value
        self.mock_chat_completions_create = self.mock_openai_client_instance.chat.completions.create

        # Mock the response structure expected from OpenAI API
        mock_choice = MagicMock()
        mock_choice.message.content = "Mocked AI response from actual RAGService call."
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        self.mock_chat_completions_create.return_value = mock_completion

        # Patch OPENAI_API_KEY in settings
        self.settings_patcher = patch('django.conf.settings.OPENAI_API_KEY', 'dummy-api-key')
        self.settings_patcher.start()

        # Create a User first, as UserProfile has a OneToOneField to User
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser_rag', password='testpass')

        self.user_profile = UserProfile.objects.create(
            user=self.user,
            display_name="Test Persona",
            bio="A test persona for RAG queries."
        )

        # Create a Document owned by the user (without a file initially to avoid FieldError)
        self.document = Document.objects.create(
            owner=self.user,
            title="Test Document for RAG",
            document_type="other",
        )
        # Mock the file field after creation to prevent actual file operations
        self.document.file = MagicMock()
        self.document.file.path = "/tmp/dummy_file.txt"
        # No need to call save() again after mocking the file field, as it's already saved.
        # If we need to ensure the mocked file is "saved", we can mock the save method too,
        # but for this context, just setting the path should be enough for RagService.

        self.url = reverse('rag-query')
        yield
        self.embedding_patcher.stop()
        self.openai_patcher.stop()
        self.settings_patcher.stop()

    def test_rag_query_success(self):
        # Create a dummy DocumentChunk for the RAG service to retrieve
        from ai_interviewee.models import DocumentChunk
        DocumentChunk.objects.create(
            document=self.document, # Link to the created document
            content="This is a relevant document chunk.",
            embedding=[0.1] * 1536,
            chunk_index=0
        )

        response = self.client.get(
            f'{self.url}?question=Hello&persona_id={self.user_profile.id}'
        )
        assert response.status_code == 200

        # TODO: Need to work out how to do a VCR equivalent test here
        # https://vcrpy.readthedocs.io/en/latest/
        # assert response.data['response'] == "Mocked AI response from actual RAGService call."
        self.mock_generate_embedding.assert_called_once_with("Hello")
        # self.mock_chat_completions_create.assert_called_once()

    def test_rag_query_missing_question(self):
        response = self.client.get(f'{self.url}?persona_id={self.user_profile.id}')
        assert response.status_code == 400
        assert response.data['error'] == 'A "question" query parameter is required.'
        self.mock_generate_embedding.assert_not_called()
        self.mock_chat_completions_create.assert_not_called()

    def test_rag_query_missing_persona_id(self):
        response = self.client.get(f'{self.url}?question=Hello')
        assert response.status_code == 400
        assert response.data['error'] == 'A "persona_id" query parameter is required.'
        self.mock_generate_embedding.assert_not_called()
        self.mock_chat_completions_create.assert_not_called()

    def test_rag_query_persona_not_found(self):
        response = self.client.get(f'{self.url}?question=Hello&persona_id=99999') # Non-existent ID
        assert response.status_code == 404
        assert response.data['error'] == 'Persona with ID 99999 not found.'
        self.mock_generate_embedding.assert_not_called()
        self.mock_chat_completions_create.assert_not_called()

    def test_rag_query_rag_service_exception(self):
        # Simulate an error within the RagService's call method
        # This will now be caught by the RagService's internal try-except blocks
        # For this test, we'll simulate an error during embedding generation
        self.mock_generate_embedding.side_effect = Exception("Embedding service error")

        response = self.client.get(
            f'{self.url}?question=Hello&persona_id={self.user_profile.id}'
        )
        assert response.status_code == 500
        assert response.data['error'] == 'An error occurred while processing your query.'
        self.mock_generate_embedding.assert_called_once()
        self.mock_chat_completions_create.assert_not_called() # Should not be called if embedding fails
