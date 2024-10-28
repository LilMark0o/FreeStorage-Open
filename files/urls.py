# authentication/urls.py
from django.urls import path
from .views import *  # Import the view

urlpatterns = [
    path('', checkFilesView, name='files'),
    path('download-all-files/', download_db_files, name='download_db_files'),
    path('download-all-chuncks/', download_db_chuncks, name='download_db_chuncks'),
    path('delete/<int:id>', deleteFile, name='delete_file'),
    path('download/<int:id>', downloadFile, name='download_file'),
    path('check_task_status', check_task_status, name='check_task_status'),
    path('task-status/', check_task_status_ajax, name='check_task_status_ajax'),
    path('download-ready/<path:file_path>/',
         download_ready_file, name='download_ready_file'),
    path('delete_folder/<path:file_path>/', delete_folder_after_download,
         name='delete_folder_after_download'),
    path('detail/<int:file_id>/', file_detail, name='file_detail'),
    path('new-tag/<int:file_id>/', new_tag, name='add_tag'),
    path('delete-tag/<int:file_id>/<int:tag_id>/',
         delete_tag, name='delete_tag'),
    path('share/<int:file_id>/', share_file, name='share_file'),
    path('shared-files/', shared_files_list, name='shared_files_list'),
    path('shared/<str:share_link>/', access_shared_file, name='access_shared_file'),
    path('shared/delete_shared_file/<int:share_link>/',
         delete_shared_file, name='delete_shared_file'),
    path('shared-error/', shared_error, name='shared_error'),

]
