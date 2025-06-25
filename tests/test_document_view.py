from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from django.contrib.auth.models import User
from ai_interviewee.models import Document, UserProfile
from datetime import datetime

class DocumentViewTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.user_profile = UserProfile.objects.create(user=self.user, display_name='Test Persona')
        self.document1 = Document.objects.create(
            title='Test Document 1',
            owner=self.user,
            document_type='pdf',
            processing_status='completed',
            uploaded_at=datetime(2023, 1, 1, 10, 0, 0)
        )
        self.document2 = Document.objects.create(
            title='Test Document 2',
            owner=self.user,
            document_type='docx',
            processing_status='completed',
            uploaded_at=datetime(2023, 1, 2, 11, 0, 0)
        )

    def test_get_documents_unauthenticated(self):
        """
        Ensure unauthenticated users cannot access the endpoint.
        """
        self.client.logout()
        response = self.client.get('/api/documents/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_documents_success(self):
        """
        Ensure we can retrieve documents successfully for the authenticated user.
        """
        response = self.client.get('/api/documents/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('response', response.data)
        self.assertEqual(len(response.data['response']), 2)
        self.assertEqual(response.data['response'][0]['name'], 'Test Document 1')
        self.assertEqual(response.data['response'][1]['name'], 'Test Document 2')
        self.assertEqual(response.data['response'][0]['type'], 'pdf')
        self.assertEqual(response.data['response'][1]['type'], 'docx')
