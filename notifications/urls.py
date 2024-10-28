# authentication/urls.py
from django.urls import path
from .views import *  # Import the view

urlpatterns = [
    path('', viewNotifications, name='notifications'),
]
