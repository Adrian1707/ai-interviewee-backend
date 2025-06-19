import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from ai_interviewee.models import Document, DocumentChunk
from ai_interviewee.tasks import process_document_task, generate_embedding_task

@pytest.fixture
def mock_document():
    """Fixture for a mock Document object."""
    doc = MagicMock(spec=Document)
    doc.id = 1
    doc.file.path = '/path/to/mock_document.txt'
    doc.processing_status = 'pending'
    doc.save = MagicMock()
    return doc

@pytest.fixture
def mock_chunk():
    """Fixture for a mock DocumentChunk object."""
    chunk = MagicMock(spec=DocumentChunk)
    chunk.id = 101
    chunk.content = "test content"
    chunk.save = MagicMock()
    return chunk

@pytest.mark.django_db
class TestProcessDocumentTask:

    @patch('ai_interviewee.tasks.extract_text_from_file')
    @patch('ai_interviewee.tasks.chunk_text')
    @patch('ai_interviewee.tasks.DocumentChunk.objects.create')
    @patch('ai_interviewee.tasks.generate_embedding_task.delay')
    @patch('ai_interviewee.tasks.Document.objects.get')
    def test_successful_processing(self, mock_get_document, mock_generate_embedding_task_delay,
                                   mock_create_document_chunk, mock_chunk_text,
                                   mock_extract_text_from_file, mock_document):
        
        mock_get_document.return_value = mock_document
        mock_extract_text_from_file.return_value = "This is some test content."
        mock_chunk_text.return_value = [
            {'content': 'chunk 1', 'page_number': 1},
            {'content': 'chunk 2', 'page_number': 1}
        ]
        mock_create_document_chunk.return_value = MagicMock(spec=DocumentChunk, id=101)

        # Call the task
        process_document_task(mock_document.id)

        # Assertions
        mock_get_document.assert_called_once_with(id=mock_document.id)
        
        # Check status updates
        assert mock_document.processing_status == 'completed'
        assert mock_document.processed_at is not None
        assert mock_document.save.call_count == 2

        mock_extract_text_from_file.assert_called_once_with(mock_document.file.path)
        mock_chunk_text.assert_called_once_with("This is some test content.")
        
        assert mock_create_document_chunk.call_count == 2
        assert mock_generate_embedding_task_delay.call_count == 2

    # @patch('ai_interviewee.tasks.Document.objects.get')
    # def test_document_does_not_exist(self, mock_get_document):
    #     mock_get_document.side_effect = Document.DoesNotExist

    #     with pytest.raises(Document.DoesNotExist):
    #         process_document_task(999) # Non-existent ID

    #     mock_get_document.assert_called_once_with(id=999)

    # @patch('ai_interviewee.tasks.extract_text_from_file')
    # @patch('ai_interviewee.tasks.Document.objects.get')
    # def test_no_text_content_extracted(self, mock_get_document, mock_extract_text_from_file):
    #     mock_document = MagicMock(spec=Document)
    #     mock_document.id = 1
    #     mock_document.file.path = '/path/to/mock_document.txt'
    #     mock_document.processing_status = 'pending'
    #     mock_document.save = MagicMock()
    #     mock_get_document.return_value = mock_document
    #     mock_extract_text_from_file.return_value = "" # No text extracted

    #     # Mock the task's self.retry method
    #     mock_self = MagicMock()
    #     mock_self.retry.side_effect = Exception("Task retry triggered") # Simulate retry raising an exception

    #     with pytest.raises(Exception, match="Task retry triggered"):
    #         process_document_task(mock_self, mock_document.id) # Call the task directly with mock_self

    #     mock_document.save.assert_called()
    #     assert mock_document.processing_status == 'failed'
    #     assert "No text content could be extracted" in mock_document.processing_error
    #     mock_self.retry.assert_called_once()

    # @patch('ai_interviewee.tasks.extract_text_from_file')
    # @patch('ai_interviewee.tasks.chunk_text')
    # @patch('ai_interviewee.tasks.Document.objects.get')
    # def test_chunk_text_raises_exception(self, mock_get_document, mock_chunk_text, mock_extract_text_from_file):
    #     mock_document = MagicMock(spec=Document)
    #     mock_document.id = 1
    #     mock_document.file.path = '/path/to/mock_document.txt'
    #     mock_document.processing_status = 'pending'
    #     mock_document.save = MagicMock()
    #     mock_get_document.return_value = mock_document
    #     mock_extract_text_from_file.return_value = "Some text."
    #     mock_chunk_text.side_effect = Exception("Chunking failed")

    #     mock_self = MagicMock()
    #     mock_self.retry.side_effect = Exception("Task retry triggered")

    #     with pytest.raises(Exception, match="Task retry triggered"):
    #         process_document_task(mock_self, mock_document.id)

    #     mock_document.save.assert_called()
    #     assert mock_document.processing_status == 'failed'
    #     assert "Chunking failed" in mock_document.processing_error
    #     mock_self.retry.assert_called_once()

    # @patch('ai_interviewee.tasks.extract_text_from_file')
    # @patch('ai_interviewee.tasks.chunk_text')
    # @patch('ai_interviewee.tasks.DocumentChunk.objects.create')
    # @patch('ai_interviewee.tasks.Document.objects.get')
    # def test_document_chunk_creation_raises_exception(self, mock_get_document, mock_create_document_chunk,
    #                                                   mock_chunk_text, mock_extract_text_from_file):
    #     mock_document = MagicMock(spec=Document)
    #     mock_document.id = 1
    #     mock_document.file.path = '/path/to/mock_document.txt'
    #     mock_document.processing_status = 'pending'
    #     mock_document.save = MagicMock()
    #     mock_get_document.return_value = mock_document
    #     mock_extract_text_from_file.return_value = "Some text."
    #     mock_chunk_text.return_value = [{'content': 'chunk 1'}]
    #     mock_create_document_chunk.side_effect = Exception("DB error on chunk create")

    #     mock_self = MagicMock()
    #     mock_self.retry.side_effect = Exception("Task retry triggered")

    #     with pytest.raises(Exception, match="Task retry triggered"):
    #         process_document_task(mock_self, mock_document.id)

    #     mock_document.save.assert_called()
    #     assert mock_document.processing_status == 'failed'
    #     assert "DB error on chunk create" in mock_document.processing_error
    #     mock_self.retry.assert_called_once()

    # @patch('ai_interviewee.tasks.extract_text_from_file')
    # @patch('ai_interviewee.tasks.chunk_text')
    # @patch('ai_interviewee.tasks.DocumentChunk.objects.create')
    # @patch('ai_interviewee.tasks.generate_embedding_task.delay')
    # @patch('ai_interviewee.tasks.Document.objects.get')
    # def test_generate_embedding_task_delay_raises_exception(self, mock_get_document, mock_generate_embedding_task_delay,
    #                                                         mock_create_document_chunk, mock_chunk_text,
    #                                                         mock_extract_text_from_file):
    #     mock_document = MagicMock(spec=Document)
    #     mock_document.id = 1
    #     mock_document.file.path = '/path/to/mock_document.txt'
    #     mock_document.processing_status = 'pending'
    #     mock_document.save = MagicMock()
    #     mock_get_document.return_value = mock_document
    #     mock_extract_text_from_file.return_value = "Some text."
    #     mock_chunk_text.return_value = [{'content': 'chunk 1'}]
    #     mock_create_document_chunk.return_value = MagicMock(spec=DocumentChunk, id=101)
    #     mock_generate_embedding_task_delay.side_effect = Exception("Celery error on delay")

    #     mock_self = MagicMock()
    #     mock_self.retry.side_effect = Exception("Task retry triggered")

    #     with pytest.raises(Exception, match="Task retry triggered"):
    #         process_document_task(mock_self, mock_document.id)

    #     mock_document.save.assert_called()
    #     assert mock_document.processing_status == 'failed'
    #     assert "Celery error on delay" in mock_document.processing_error
    #     mock_self.retry.assert_called_once()
