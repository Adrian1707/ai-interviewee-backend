from django.shortcuts import render
from django.contrib import admin
import os
from . import views
from django.conf import settings

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.utils import timezone
from .models import Document, UserProfile
from .tasks import process_document_task
from .serializers import DocumentUploadSerializer, DocumentSerializer
from .services.rag_service import RagService
import logging

logger = logging.getLogger(__name__)

def home(request):
    """Render a form for the user to upload a document"""
    return render(request, 'home.html')


class DocumentUploadView(APIView):
    """
    API endpoint for uploading documents
    """
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, *args, **kwargs):
        serializer = DocumentUploadSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            try:
                # Save the document
                document = serializer.save()
                
                # Trigger async processing
                process_document_task.delay(document.id)
                
                logger.info(f"Document {document.id} uploaded and queued for processing")
                
                # Return document details
                response_serializer = DocumentSerializer(
                    document, 
                    context={'request': request}
                )
                
                return Response(
                    {
                        'message': 'Document uploaded successfully and queued for processing',
                        'document': response_serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
                
            except Exception as e:
                logger.error(f"Error uploading document: {str(e)}")
                return Response(
                    {'error': 'Failed to upload document'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DocumentView(APIView):
    """
        API endpoint for getting user documents
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        persona_id = request.query_params.get('persona_id', None)
        
        if not persona_id:
            return Response({'error': 'Missing persona_id parameter'}, status=status.HTTP_400_BAD_REQUEST)
        user_profile = UserProfile.objects.filter(id=persona_id).first()
        
        if not user_profile:
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)

        user = user_profile.user
        user_documents = Document.objects.filter(owner=user)

        response = [
            {"title": doc.title, "uploaded_at": doc.uploaded_at, "document_type": doc.document_type}
            for doc in user_documents
        ]

        return Response(
                {'response': response},
                status=status.HTTP_200_OK
            )


class RagQueryView(APIView):
    """
    API endpoint for querying the RAG service.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        question = request.query_params.get('question', None)
        persona_id = request.query_params.get('persona_id', None)

        if not question:
            return Response(
                {'error': 'A "question" query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not persona_id:
            return Response(
                {'error': 'A "persona_id" query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            persona = UserProfile.objects.get(id=persona_id)
        except UserProfile.DoesNotExist:
            return Response(
                {'error': f'Persona with ID {persona_id} not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving persona: {e}")
            return Response(
                {'error': 'An error occurred while retrieving the persona.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            rag_service = RagService()
            response_text = rag_service.call(question, persona)
            return Response(
                {'response': response_text},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error calling RAG service: {e}")
            return Response(
                {'error': 'An error occurred while processing your query.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
