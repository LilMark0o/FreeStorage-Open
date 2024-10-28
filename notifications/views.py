from celery import shared_task
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from upload.models import Notificacions


@login_required  # Ensure the user is authenticated
def viewNotifications(request):
    user = request.user

    # Get all new notifications (shown=False)
    newNotificacions = list(
        Notificacions.objects.filter(user=user, shown=False))

    # Fetch the old notifications after marking new ones as shown
    oldNotificacions = list(Notificacions.objects.filter(
        user=user, shown=True).order_by('-date', '-id'))

    # Mark all new notifications as shown in one go
    Notificacions.objects.filter(user=user, shown=False).update(shown=True)

    if len(newNotificacions) == 0 and len(oldNotificacions) == 0:
        notificationsAtAll = False
    else:
        notificationsAtAll = True

    return render(request, 'notifications/notifications.html', {
        'newNotificacions': newNotificacions,
        'oldNotificacions': oldNotificacions,
        'notificationsAtAll': notificationsAtAll
    })
