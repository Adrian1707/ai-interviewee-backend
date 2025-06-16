from django.shortcuts import render
from django.contrib import admin
import os
from . import views

from django.http import StreamingHttpResponse
from django.shortcuts import render
import time
from django.conf import settings

def home(request):
    """Render a form for the user to submit a debate topic."""
    return render(request, 'home.html')

    """Decode bytes to UTF-8, replacing invalid characters."""
    if isinstance(data, bytes):
        return data.decode('utf-8', errors='replace')
    return data