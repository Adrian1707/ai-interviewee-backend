from django.shortcuts import render
from django.contrib import admin
import os
from . import views
from django.conf import settings
from django.contrib.auth.models import User

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from django.utils import timezone
from .models import Document, UserProfile
from .tasks import process_document_task
from .serializers import DocumentUploadSerializer, DocumentSerializer, RegisterSerializer, LoginSerializer, UserSerializer
from .services.rag_service import RagService
import logging
from django.contrib.auth import login, logout

logger = logging.getLogger(__name__)

def home(request):
    """Render a form for the user to upload a document"""
    return render(request, 'home.html')

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_data = serializer.save()
        return Response(user_data, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

class CurrentUserView(APIView):
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class DocumentUploadView(APIView):
    """
    API endpoint for uploading documents
    """
    permission_classes = [permissions.IsAuthenticated]
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
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_documents = Document.objects.filter(owner=request.user).order_by('uploaded_at')

        response = [
            {"name": doc.title, "status": doc.processing_status, "type": doc.document_type}
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
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        question = request.query_params.get('question', None)

        if not question:
            return Response(
                {'error': 'A "question" query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            rag_service = RagService()
            response_text = rag_service.call(question, request.user.profile)
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
