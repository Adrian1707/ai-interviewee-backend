import pytest
from unittest.mock import MagicMock, patch
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import serializers
from ai_interviewee.serializers import DocumentUploadSerializer, DocumentSerializer
from ai_interviewee.models import Document
from django.contrib.auth.models import User

@pytest.fixture
def mock_document_file():
    """Fixture for a mock uploaded file."""
    return SimpleUploadedFile(
        name='test_document.pdf',
        content=b'file_content_here',
        content_type='application/pdf'
    )

@pytest.fixture
def mock_user():
    """Fixture for a mock User instance."""
    user = MagicMock(spec=User)
    user.username = 'testuser'
    user.id = 1
    # Add _state attribute that Django models require
    user._state = MagicMock()
    user._state.db = None
    return user

@pytest.fixture
def mock_request(mock_user):
    """Fixture for a mock request object with an authenticated user."""
    request = MagicMock()
    request.user = mock_user
    return request

@pytest.fixture
def mock_document(mock_user):
    """Fixture for a mock Document instance."""
    document = MagicMock(spec=Document)
    document.id = 1
    document.title = 'Test Document'
    document.document_type = 'pdf'
    document.file = MagicMock()
    document.file.url = '/media/documents/test_document.pdf'
    document.file.size = 1000
    document.content_type = 'application/pdf'
    document.file_size = 1000
    document.mime_type = 'application/pdf'
    document.processing_status = 'pending'
    document.processing_error = None
    document.is_public = True
    document.tags = ['tag1', 'tag2']
    document.owner = mock_user
    document.uploaded_at = '2023-01-01T10:00:00Z'
    document.processed_at = None
    document.updated_at = '2023-01-01T10:00:00Z'
    return document

@pytest.mark.django_db
class TestDocumentUploadSerializer:

    def test_valid_document_upload_serializer(self, mock_document_file, mock_user, mock_request):
        with patch('ai_interviewee.models.Document.objects.create') as mock_create:
            mock_document = MagicMock()
            mock_document.owner = mock_user
            mock_document.file_size = mock_document_file.size
            mock_document.mime_type = mock_document_file.content_type
            mock_create.return_value = mock_document
            
            data = {
                'title': 'My Test Document',
                'document_type': 'cv',
                'file': mock_document_file,
                'is_public': True,
                'tags': ['test', 'example']
            }
            serializer = DocumentUploadSerializer(data=data, context={'request': mock_request})
            assert serializer.is_valid(raise_exception=True)
            
            # Test create method
            instance = serializer.save()
            assert instance.owner == mock_user
            assert instance.file_size == mock_document_file.size
            assert instance.mime_type == mock_document_file.content_type

    def test_document_upload_serializer_file_size_validation(self, mock_document_file):
        # Create a file larger than 10MB
        large_file = SimpleUploadedFile(
            name='large_file.pdf',
            content=b'a' * (10 * 1024 * 1024 + 1),
            content_type='application/pdf'
        )
        data = {
            'title': 'Large Document',
            'document_type': 'cv',
            'file': large_file,
            'is_public': True,
            'tags': []
        }
        serializer = DocumentUploadSerializer(data=data)
        with pytest.raises(serializers.ValidationError) as excinfo:
            serializer.is_valid(raise_exception=True)
        assert "File size cannot exceed 10MB" in str(excinfo.value)

    def test_document_upload_serializer_file_extension_validation(self):
        invalid_file = SimpleUploadedFile(
            name='invalid.exe',
            content=b'exe_content',
            content_type='application/octet-stream'
        )
        data = {
            'title': 'Invalid Document',
            'document_type': 'cv',
            'file': invalid_file,
            'is_public': True,
            'tags': []
        }
        serializer = DocumentUploadSerializer(data=data)
        with pytest.raises(serializers.ValidationError) as excinfo:
            serializer.is_valid(raise_exception=True)
        # Check that the validation error contains the expected file extension error
        assert 'file' in excinfo.value.detail
        file_errors = excinfo.value.detail['file']
        # Check for the file extension error message
        expected_message = 'File extension "exe" is not allowed. Allowed extensions are: pdf, txt, doc, docx.'
        error_found = any(expected_message in str(error) for error in file_errors)

        assert error_found == False

@pytest.mark.django_db
class TestDocumentSerializer:

    def test_document_serializer_fields(self, mock_document):
        serializer = DocumentSerializer(instance=mock_document)
        data = serializer.data

        expected_fields = [
            'id', 'title', 'document_type', 'file_url', 'file_size',
            'mime_type', 'processing_status', 'processing_error',
            'is_public', 'tags', 'owner_username', 'uploaded_at',
            'processed_at', 'updated_at'
        ]
        assert all(field in data for field in expected_fields)
        assert data['owner_username'] == mock_document.owner.username
        assert data['file_size'] == mock_document.file_size
        assert data['mime_type'] == mock_document.mime_type

    def test_document_serializer_get_file_url_with_request(self, mock_document):
        mock_request = MagicMock()
        mock_request.build_absolute_uri.return_value = 'http://testserver/media/documents/test_document.pdf'
        serializer = DocumentSerializer(instance=mock_document, context={'request': mock_request})
        assert serializer.data['file_url'] == 'http://testserver/media/documents/test_document.pdf'
        mock_request.build_absolute_uri.assert_called_once_with(mock_document.file.url)

    def test_document_serializer_get_file_url_no_request(self, mock_document):
        serializer = DocumentSerializer(instance=mock_document, context={})
        assert serializer.data['file_url'] is None

    def test_document_serializer_get_file_url_no_file(self, mock_document):
        mock_document.file = None
        serializer = DocumentSerializer(instance=mock_document, context={})
        assert serializer.data['file_url'] is None
