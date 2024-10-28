import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
import os
import uuid

from free_storage import settings
from .models import File, SharedFile
from django.utils import timezone
from django.http import HttpResponse, FileResponse, Http404
from django.shortcuts import render, redirect
import math
from django.http import JsonResponse
from django.http import FileResponse, Http404
from celery.result import AsyncResult
from django.shortcuts import redirect
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from upload.models import File, Tags
from .utils import *


def deleteOldFolders():
    # Get the path to the folder where the files are stored
    def deleteFromBase(folder_path):
        foldersInside = os.listdir(folder_path)
        if len(foldersInside) < 2:
            return
        dateNow = str(datetime.datetime.now().date())
        for folder in foldersInside:
            if folder != dateNow:
                shutil.rmtree(folder_path + folder)
    deleteFromBase('downloads/')
    deleteFromBase('uploads/')


def save_all_db(request):
    files = File.objects.all()
    dataFrameFiles = []
    for file in files:
        dataFrameFiles.append({
            'id': file.id,
            'file_name': file.file_name,
            'size': file.size,
            'date': file.date,
            'uploading': file.uploading,
            'user': file.user.username
        })
    df_files = pd.DataFrame(dataFrameFiles)
    chuncks = Chunk.objects.all()
    dataFrameChuncks = []
    for chunck in chuncks:
        dataFrameChuncks.append({
            'id': chunck.id,
            'file': chunck.file.id,
            'decrypted_data': chunck.get_decrypted_message()
        })
    df_chuncks = pd.DataFrame(dataFrameChuncks)
    # Create directory if it doesn't exist
    save_dir = 'allDB'
    os.makedirs(save_dir, exist_ok=True)

    # Save the CSV files
    files_csv_path = os.path.join(save_dir, 'files.csv')
    chunks_csv_path = os.path.join(save_dir, 'chunks.csv')

    df_files.to_csv(files_csv_path, index=False)
    df_chuncks.to_csv(chunks_csv_path, index=False)


@login_required
def download_db_files(request):
    user = request.user
    if user.username != 'marcoAdmin':
        return redirect('files')
    save_all_db(request)
    # Get the path to the folder where the files are stored
    folder_path = 'allDB'

    # Check if the folder exists
    if not os.path.exists(folder_path):
        messages.error(request, 'Files not found')
        return redirect('files')

    # Create a file response for downloading the file
    response = FileResponse(open(folder_path + '/files.csv', 'rb'))
    response['Content-Disposition'] = f'attachment; filename="files.csv"'
    return response


@login_required
def download_db_chuncks(request):
    user = request.user
    if user.username != 'marcoAdmin':
        return redirect('files')
    # Get the path to the folder where the files are stored
    folder_path = 'allDB'
    save_all_db(request)

    # Check if the folder exists
    if not os.path.exists(folder_path):
        messages.error(request, 'Files not found')
        return redirect('files')

    # Create a file response for downloading the file
    response = FileResponse(open(folder_path + '/chunks.csv', 'rb'))
    response['Content-Disposition'] = f'attachment; filename="chunks.csv"'
    return response


def checkFilesView(request):
    deleteOldFolders()
    if not request.user.is_authenticated:
        return redirect('home')
    user = request.user
    # Get search parameters from the GET request
    search_name = request.GET.get('search_name', '')
    search_tag = request.GET.get('search_tag', '')

    # Filter files by user and order them by date and ID
    files = File.objects.filter(user=user).order_by('-date', '-id')

    # If there's a search term for the file name, filter the files by name
    if search_name:
        files = files.filter(file_name__icontains=search_name)

    # If there's a search term for tags, filter the files by tags
    if search_tag:
        files = files.filter(tags__tag__icontains=search_tag).distinct()

    # If no files are found, set an empty list
    if len(files) == 0:
        files = []
    else:
        for file in files:
            # Get the tags for each file
            file.tags_list = file.tags.all()
            if len(file.tags_list) > 0:
                file.hasTags = True
                file.tags_list = file.tags_list[:3]
            else:
                file.hasTags = False

            # Calculate upload percentage
            if file.uploading:
                chuncksOfThisFile = Chunk.objects.filter(file=file)
                file.percentage = str(round(
                    (len(chuncksOfThisFile) / math.ceil(int(file.size) / ((2**(10*2))*18))) * 100, 2)) + '%'
                if file.percentage == '100.0%':
                    file.percentage = '99.99%'
                if round(
                        (len(chuncksOfThisFile) / math.ceil(int(file.size) / ((2**(10*2))*18))) * 100, 2) > 100:
                    file.percentage = '99.99%'

            # Format file size and shorten file name if too long
            file.size = readableSize(file.size)
            if len(file.file_name) > 15:
                file.file_name = file.file_name[:15] + '...'
    if search_name != '' or search_tag != '':
        filtred = True
    else:
        filtred = False
    userTags = Tags.objects.filter(user=user).distinct()
    return render(request, 'files/checkFiles.html', {'files': files, 'search_name': search_name, 'search_tag': search_tag, 'filtred': filtred, 'user_tags': userTags})


@login_required
def deleteFile(request, id):
    if request.method != 'POST':
        return redirect('files')
    user = request.user
    if not File.objects.filter(id=id, user=user).exists():
        messages.error(request, 'File not found')
        return redirect('files')
    file = File.objects.get(id=id)
    file.delete()
    messages.success(request, 'File deleted successfully')
    return redirect('files')


@login_required
def downloadFile(request, id):
    user = request.user
    deleteOldFolders()
    if not File.objects.filter(id=id, user=user).exists():
        messages.error(request, 'File not found')
        return redirect('files')
    file = File.objects.get(id=id)

    task = bigDownloadTask.delay(file.id, user.username)

    # Pass the task ID to the template
    context = {
        'task_id': task.id,
        'file_id': file.id
    }
    return render(request, 'files/download_status.html', context)


def recreate_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)

    os.makedirs(folder_path)


"""
OLD

@login_required
def download_ready_file(request, file_path):
    try:
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{
            file_path.split("/")[-1]}"'
        return response

    except FileNotFoundError:
        raise Http404("File not found")
"""


def download_ready_file(request, file_path):
    # Get the folder path from the file path
    folder_path = os.path.dirname(file_path)

    try:
        # Create a file response for downloading the file
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{
            file_path.split("/")[-1]}"'
        if request.session.get('download-key'):
            key = request.session['download-key']
            sharedFile = SharedFile.objects.get(share_link=key)
            sharedFile.increment_download()
            del request.session['download-key']
            print('I got here to increment download')
        else:
            print('I got here to not increment download')
        return response

    except FileNotFoundError:
        raise Http404("File not found")

    # Note: We can't directly delete the folder here since the response is already returned.


def recreate_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path)


def delete_folder_after_download(request, file_path):
    # Assuming you want to delete the folder
    folder_path = os.path.dirname(file_path)

    # Call the function to recreate the folder
    recreate_folder(folder_path)
    return redirect('files')


def checkFilesInFolder(folder_path):
    usableFiles = [x for x in os.listdir(
        folder_path) if 'your_downloaded_file_' not in x]
    return len(usableFiles)


def howManyPercentageOfDownload(file_id, request):
    file = File.objects.get(id=file_id)
    if request.user.is_authenticated:
        username = request.user.username
    else:
        username = 'anonymous'
    chuncksOfThisFile = len(Chunk.objects.filter(file=file))
    downloadedChuncs = checkFilesInFolder(
        f'downloads/{str(datetime.datetime.now().date())}/{username}/{file_id}')
    percentage = downloadedChuncs/chuncksOfThisFile
    if percentage >= 1:
        return 0.99
    if percentage < 0.01:
        return 0.01
    return round((downloadedChuncs/chuncksOfThisFile)*100)


def check_task_status_ajax(request):
    # Get the task_id from the GET request
    """CALL howMany"""
    task_id = request.GET.get('task_id')

    if not task_id:
        return JsonResponse({'status': 'FAILURE', 'message': 'Task ID not provided.', 'progress': 0})

    # Your logic to check task status...
    # Assuming you have a function to get the task status:
    task_result = AsyncResult(task_id)

    if task_result.ready():
        if task_result.successful():
            # Assume the result is the file path
            return JsonResponse({'status': 'SUCCESS', 'file_path': task_result.result, 'progress': 100})
        else:
            return JsonResponse({'status': 'FAILURE', 'message': 'Task failed.', 'progress': 0})
    else:
        file_id = request.GET.get('file_id')
        percentage = howManyPercentageOfDownload(file_id, request)
        return JsonResponse({'status': 'PENDING', 'message': 'Task is still processing.', 'progress': percentage})


@login_required
def check_task_status(request):
    task_id = request.session.get('celery_task_id')
    if not task_id:
        return Http404("Task not found")

    # Get the Celery task result
    task = AsyncResult(task_id)

    if task.state == 'SUCCESS':
        # The file is ready, return it for download
        file_path = task.result

        # Check if the file exists
        try:
            response = FileResponse(open(file_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{
                file_path.split("/")[-1]}"'
            if request.session.get('download-key'):
                key = request.session['download-key']
                sharedFile = SharedFile.objects.get(share_link=key)
                sharedFile.increment_download()
                del request.session['download-key']
                print('I got here to increment download')
            else:
                print('I got here to not increment download')
            return response
        except FileNotFoundError:
            return HttpResponse("File not found", status=404)

    elif task.state == 'FAILURE':
        return HttpResponse("Task failed", status=500)

    else:
        # Task is still running, return a message or a loading page
        return HttpResponse("Task is still in progress. Please wait...", status=202)


@login_required
def file_detail(request, file_id):
    file = File.objects.filter(user=request.user, id=file_id)
    if len(file) == 0:
        messages.error(request, 'File not found')
        return redirect('files')
    else:
        file = file[0]
        file.size = readableSize(file.size)
        shareLink = SharedFile.objects.filter(file=file)
        if len(shareLink) > 0:
            file.link = shareLink[0].share_link
        else:
            file.link = None

    if request.method == 'POST':
        tag_name = request.POST.get('tag')
        if tag_name:
            tag, created = Tags.objects.get_or_create(
                tag=tag_name, user=request.user)
            file.tags.add(tag)
            messages.success(request, 'Tag added successfully!')
            return redirect('file_detail', file_id=file.id)

    user_tags = Tags.objects.filter(user=request.user).distinct()
    fileTags = file.tags.all()
    if len(fileTags) > 0:
        file.hasTags = True
        file.tags_list = fileTags
    else:
        file.hasTags = False

    context = {
        'file': file,
        'user_tags': user_tags,  # Pass the tags to the template
    }
    return render(request, 'files/fileDetail.html', context)


@login_required
def new_tag(request, file_id):
    file = File.objects.filter(user=request.user, id=file_id)
    if len(file) == 0:
        messages.error(request, 'File not found')
        return redirect('files')
    else:
        file = file[0]
    tag_name = request.POST.get('tag')
    if tag_name:
        if len(tag_name) > 30:
            messages.error(request, 'Tag name is too long!')
            return redirect('file_detail', file_id=file.id)
        tag_name = tag_name.lower()
        tag, created = Tags.objects.get_or_create(
            tag=tag_name, user=request.user)
        file.tags.add(tag)
        messages.success(request, 'Tag added successfully!')
    return redirect('file_detail', file_id=file.id)


@login_required
def delete_tag(request, file_id, tag_id):
    file = File.objects.filter(user=request.user, id=file_id)
    if len(file) == 0:
        messages.error(request, 'File not found')
        return redirect('files')
    else:
        file = file[0]
    tag = Tags.objects.filter(user=request.user, id=tag_id)
    if len(tag) == 0:
        messages.error(request, 'Tag not found')
        return redirect('file_detail', file_id=file_id)
    else:
        tag = tag[0]

    # Remover el tag del archivo
    file.tags.remove(tag)

    # Si el tag no está asociado a ningún otro archivo, eliminarlo
    if not File.objects.filter(tags=tag).exists():
        tag.delete()

    messages.success(request, 'Tag removed successfully!')
    return redirect('file_detail', file_id=file_id)


def readableSize(bytes):
    bytes = float(bytes)
    kilobyte = 1024
    megabyte = kilobyte * 1024
    gigabyte = megabyte * 1024
    tera = gigabyte * 1024

    if bytes < kilobyte:
        return f'{bytes} B'
    elif kilobyte <= bytes < megabyte:
        return f'{bytes / kilobyte:.2f} KB'
    elif megabyte <= bytes < gigabyte:
        return f'{bytes / megabyte:.2f} MB'
    elif gigabyte <= bytes < tera:
        return f'{bytes / gigabyte:.2f} GB'
    elif tera <= bytes:
        terasNumber = bytes / tera
        if terasNumber > 99:
            return f'+99 TB'
        else:
            return f'{terasNumber:.2f} TB'

# share file stuff


@login_required
def share_file(request, file_id):
    """View for sharing a file, creating a share link."""
    file = File.objects.filter(user=request.user, id=file_id)
    if len(file) == 0:
        messages.error(request, 'File not found')
        return redirect('files')
    else:
        file = file[0]

    if request.method == 'POST':
        expiration_date = request.POST.get('expiration_date')
        max_downloads = request.POST.get('max_downloads')
        limitless_downloads = request.POST.get('limitless_downloads', False)

        share_link = uuid.uuid4()  # Create unique share link
        if max_downloads and not max_downloads.isdigit():
            messages.error(request, 'Invalid number of downloads')
            return redirect('file_detail', file_id=file.id)
        if max_downloads and int(max_downloads) < 1:
            messages.error(
                request, 'Number of downloads must be greater than 0')
            return redirect('file_detail', file_id=file.id)
        if not limitless_downloads and not max_downloads:
            max_downloads = 1
        shared_file = SharedFile(
            file=file,
            user=request.user,
            share_link=share_link,
            expiration_date=expiration_date if expiration_date else None,
            max_downloads=int(max_downloads) if max_downloads else None,
            limitless_downloads=bool(limitless_downloads)
        )
        shared_file.save()

        messages.success(request, 'File shared successfully!')
        return redirect('shared_files_list')

    return redirect('file_detail', file_id=file.id)


def shared_error(request):
    print('I got here to shared_error views')
    return render(request, 'files/shared_error.html')


def access_shared_file(request, share_link):
    """View to access a shared file via a unique link."""
    deleteOldFolders()
    shared_file = SharedFile.objects.filter(share_link=share_link)
    if len(shared_file) == 0:
        print('I got here to shared_error views error catch 1')
        return redirect('shared_error')
    else:
        shared_file = shared_file[0]

    # Check if the link is still valid
    if not shared_file.is_valid():
        print('I got here to shared_error views error catch 2')
        return redirect('shared_error')

    # Retrieve the file path
    file = shared_file.file

    if request.user.is_authenticated:
        username = request.user.username
    else:
        username = 'anonymous'
    task = bigDownloadTask.delay(file.id, username)

    context = {
        'task_id': task.id,
        'file_id': file.id,
    }
    request.session['download-key'] = share_link
    return render(request, 'files/download_status.html', context)


@login_required
def shared_files_list(request):
    """View to list all files shared by the user."""
    shared_files = SharedFile.objects.filter(
        user=request.user).order_by('-created_at')
    if len(shared_files) == 0:
        nini = True
    else:
        nini = False
    usable = []
    old = []
    for shared_file in shared_files:
        if shared_file.is_valid():
            usable.append(shared_file)
        else:
            old.append(shared_file)

    return render(request, 'files/shared_files_list.html', {'usable': usable, 'old': old, 'nini': nini,
                                                            'numUsable': len(usable), 'numOld': len(old),
                                                            'SITE_URL': settings.SITE_URL})


@login_required
def delete_shared_file(request, share_link):
    shared_file = SharedFile.objects.filter(user=request.user, id=share_link)
    if len(shared_file) == 0:
        messages.error(request, 'File not found')
        return redirect('shared_files_list')
    else:
        shared_file = shared_file[0]

    shared_file.delete()
    messages.success(request, 'File deleted successfully')
    return redirect('shared_files_list')
