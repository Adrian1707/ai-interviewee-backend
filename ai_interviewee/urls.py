from django.contrib import admin
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('api/upload/', views.DocumentUploadView.as_view(), name='document-upload'),
    path('api/documents/', views.DocumentView.as_view(), name='document-view'),
    path('api/rag_query/', views.RagQueryView.as_view(), name='rag-query'),
    path('api/register/', views.RegisterView.as_view(), name='register'),
    path('api/login/', views.LoginView.as_view(), name='login'),
    path('api/logout/', views.LogoutView.as_view(), name='logout'),
    path('api/current_user/', views.CurrentUserView.as_view(), name='current_user'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

