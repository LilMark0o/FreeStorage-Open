# authentication/urls.py
from django.urls import path
from .views import uploadFileView  # Import the view

urlpatterns = [
    path('uploadFile/', uploadFileView, name='uploadFile'),
]
