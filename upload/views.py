import time
from celery import shared_task
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .utils import bigUploadTask
from django.contrib.auth import get_user_model
import os
User = get_user_model()


@login_required  # Ensure the user is authenticated
def uploadFileView(request):
    if request.method == "POST":
        if request.FILES.get("file"):
            uploaded_file = request.FILES["file"]
            profile = request.user.userprofile
            if profile.sizePerFile < uploaded_file.size:
                messages.error(
                    request, 'This file is too large for your current plan')
                return render(request, 'upload/upload.html')
            # Save the file temporarily to a directory
            user = request.user
            userName = user.username
            temp_dir = f'temp/{user.username}/'
            os.makedirs(temp_dir, exist_ok=True)
            temp_file_path = os.path.join(temp_dir, uploaded_file.name)

            with open(temp_file_path, 'wb+') as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)

            # Send the path of the file to the Celery task instead of the entire content
            bigUploadTask.delay(temp_file_path, userName)

            messages.success(request, f'''The file {
                             uploaded_file.name} is uploading, you will be notified when it is done''')
            return redirect('home')
        else:
            messages.error(request, 'No file was uploaded')
            return render(request, 'upload/upload.html')

    return render(request, 'upload/upload.html')
