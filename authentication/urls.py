# authentication/urls.py
from django.urls import path
from .views import *
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login/', custom_login, name='login'),
    path('logout/', LogoutView.as_view(next_page='homeInitial'), name='logout'),
    path('register/', register, name='register'),
    path('', home, name='homeInitial'),
    path('home/', home, name='home'),
    path('landing/', landing, name='landing'),
]
