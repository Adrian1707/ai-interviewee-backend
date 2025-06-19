from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/documents/upload/', views.DocumentUploadView.as_view(), name='document-upload'),
    path('api/documents/', views.DocumentView.as_view(), name='documents'),
    path('api/rag/query/', views.RagQueryView.as_view(), name='rag-query'),
]
