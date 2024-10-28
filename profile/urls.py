from django.urls import path
from .views import *

urlpatterns = [
    path('verify/<str:code>/', verify_email, name='verify_email'),
    path('', profile_view, name='profile'),
    path('delete/<int:user_id>/',
         delete_account, name='delete_account'),
    path('update/<int:pk>/', update_profile, name='update_profile'),
    path('authenticate_user/<int:pk>/', authenticate, name='authenticate_user'),

]
