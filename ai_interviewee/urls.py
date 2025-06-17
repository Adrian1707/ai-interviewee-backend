from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/documents/upload/', views.DocumentUploadView.as_view(), name='document-upload'),
]
