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
from .models import Document
from .tasks import process_document_task
from .serializers import DocumentUploadSerializer, DocumentSerializer
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

