import pytest
from unittest.mock import MagicMock, patch
from ai_interviewee.embedding_service import OpenAIEmbeddingService
import os

@pytest.fixture
def mock_openai_client():
    """Fixture to mock the OpenAI client."""
    with patch('openai.OpenAI') as mock_client_class:
        mock_client_instance = MagicMock()
        mock_client_class.return_value = mock_client_instance
        yield mock_client_instance

@pytest.fixture
def openai_embedding_service(mock_openai_client):
    """Fixture to provide an instance of OpenAIEmbeddingService with a mocked client."""
    # Ensure OPENAI_API_KEY is set for the service initialization, even if mocked
    os.environ['OPENAI_API_KEY'] = 'test_api_key' 
    service = OpenAIEmbeddingService()
    del os.environ['OPENAI_API_KEY'] # Clean up
    return service

def test_openai_embedding_service_initialization_with_env_var():
    """Test that the service initializes correctly when API key is in environment."""
    os.environ['OPENAI_API_KEY'] = 'test_env_key'
    service = OpenAIEmbeddingService()
    assert service.model == "text-embedding-3-small"
    assert service.client is not None
    del os.environ['OPENAI_API_KEY']

def test_openai_embedding_service_initialization_with_arg():
    """Test that the service initializes correctly when API key is passed as argument."""
    service = OpenAIEmbeddingService(api_key='test_arg_key')
    assert service.model == "text-embedding-3-small"
    assert service.client is not None

def test_openai_embedding_service_initialization_no_api_key():
    """Test that initialization fails if no API key is provided."""
    if 'OPENAI_API_KEY' in os.environ:
        del os.environ['OPENAI_API_KEY'] # Ensure it's not set
    with pytest.raises(ValueError, match="OpenAI API key not provided"):
        OpenAIEmbeddingService()

def test_generate_embedding_success(openai_embedding_service, mock_openai_client):
    """Test successful embedding generation."""
    mock_embedding = [0.1, 0.2, 0.3]
    mock_openai_client.embeddings.create.return_value = MagicMock(
        data=[MagicMock(embedding=mock_embedding)]
    )

    text = "This is a test sentence."
    embedding = openai_embedding_service.generate_embedding(text)

    mock_openai_client.embeddings.create.assert_called_once_with(
        input=text,
        model="text-embedding-3-small"
    )
    assert embedding == mock_embedding

def test_generate_embedding_empty_text(openai_embedding_service):
    """Test embedding generation with empty text."""
    embedding = openai_embedding_service.generate_embedding("")
    assert embedding is None

def test_generate_embedding_whitespace_text(openai_embedding_service):
    """Test embedding generation with whitespace-only text."""
    embedding = openai_embedding_service.generate_embedding("   ")
    assert embedding is None

def test_generate_embedding_unexpected_error(openai_embedding_service, mock_openai_client):
    """Test embedding generation when an unexpected error occurs."""
    mock_openai_client.embeddings.create.side_effect = Exception("Unexpected error")

    with pytest.raises(Exception, match="Unexpected error"):
        openai_embedding_service.generate_embedding("Unexpected text")
