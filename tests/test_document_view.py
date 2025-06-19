from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from django.contrib.auth.models import User
from ai_interviewee.models import Document, UserProfile
from datetime import datetime

class DocumentViewTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.user_profile = UserProfile.objects.create(user=self.user, display_name='Test Persona')
        self.document1 = Document.objects.create(
            title='Test Document 1',
            owner=self.user,
            document_type='pdf',
            uploaded_at=datetime(2023, 1, 1, 10, 0, 0)
        )
        self.document2 = Document.objects.create(
            title='Test Document 2',
            owner=self.user,
            document_type='docx',
            uploaded_at=datetime(2023, 1, 2, 11, 0, 0)
        )

    def test_get_documents_missing_persona_id(self):
        """
        Ensure we get a 400 error if persona_id is missing.
        """
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Missing persona_id parameter'})

    def test_get_documents_user_profile_not_found(self):
        """
        Ensure we get a 404 error if user profile is not found.
        """
        response = self.client.get('/api/documents/?persona_id=999') # Non-existent persona_id
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'error': 'User profile not found'})

    @patch('ai_interviewee.models.UserProfile.objects.filter')
    @patch('ai_interviewee.models.Document.objects.filter')
    def test_get_documents_success(self, mock_document_filter, mock_user_profile_filter):
        """
        Ensure we can retrieve documents successfully for a given persona_id.
        """
        # Mock UserProfile.objects.filter to return our user_profile
        mock_user_profile_filter.return_value.first.return_value = self.user_profile

        # Mock Document.objects.filter to return our documents
        mock_document_filter.return_value = [self.document1, self.document2]

        response = self.client.get(f'/api/documents/?persona_id={self.user_profile.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('response', response.data)
        self.assertEqual(len(response.data['response']), 2)
        self.assertEqual(response.data['response'][0]['title'], 'Test Document 1')
        self.assertEqual(response.data['response'][1]['title'], 'Test Document 2')
        self.assertEqual(response.data['response'][0]['document_type'], 'pdf')
        self.assertEqual(response.data['response'][1]['document_type'], 'docx')
        # Check datetime format
        
        # self.assertIn('2023-01-01T10:00:00Z', response.data['response'][0]['uploaded_at'].date().isoformat())
        # self.assertIn('2023-01-02T11:00:00Z', response.data['response'][1]['uploaded_at'].date().isoformat())
