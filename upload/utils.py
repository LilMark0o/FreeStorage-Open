from __future__ import absolute_import, unicode_literals
import datetime
import time
from celery import shared_task
from free_storage.celery import app
from dotenv import load_dotenv
from .models import Chunk, File, Notificacions  # Import the Chunk and File models
import os
import shutil
import zipfile
import telegram
from telegram import InputFile
from random import choice
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User  # Import the User model
from telegram.request import HTTPXRequest
import asyncio

# Adjust the limits as needed


@shared_task(soft_time_limit=60*60*5, time_limit=60*60*5, queue='upload_queue')
def bigUploadTask(temp_file_path, userName: str):
    DATE = str(datetime.datetime.now().date())
    request = HTTPXRequest(connect_timeout=60*60*24,
                           read_timeout=60*60*24, write_timeout=60*60*24,
                           pool_timeout=60*60*24,
                           # Increase write_timeout
                           connection_pool_size=50)  # Increase write_timeout

    load_dotenv()
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    bot = telegram.Bot(token=TOKEN, request=request)
    CHUNK_SIZE = int((1024 ** 2)) * 18  # 18MB

    def deleteFolder(folder_path):
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

    async def getRandomString(length: int):
        alphanumeric = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        return ''.join(choice(alphanumeric) for _ in range(length))

    def recreate_folder(folder_path):
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        os.makedirs(folder_path)

    def split_file(temp_file_path, chunk_size, folder=None):
        if folder is None:
            folder = 'temp_chunks'
        base_name = os.path.basename(temp_file_path)
        file_ext = base_name.split('.')[-1]
        base_name = base_name.split('.')[0]

        recreate_folder(folder)
        chunk_count = 0
        chunksPaths = []

        with open(temp_file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                chunk_count += 1
                if chunk_count >= 27:
                    extension = ''
                    chunk_count2edit = chunk_count
                    while chunk_count2edit >= 27:
                        extension += 'Z'
                        chunk_count2edit -= 27
                    extension += chr(chunk_count2edit + 66)
                    chunk_filename = f"{base_name}_chunk_{
                        extension}.{file_ext}"
                else:
                    chunk_filename = f"{base_name}_chunk_{
                        chr(chunk_count + 64)}.{file_ext}"
                chunkPath = folder + "/" + chunk_filename
                with open(chunkPath, 'wb') as chunk_file:
                    chunk_file.write(chunk)
                chunksPaths.append(chunkPath)

        return chunksPaths

    async def uploadFile(temp_file_path, userName: str) -> str:
        user = await sync_to_async(User.objects.get)(username=userName)
        file_instance = File(
            file_name=os.path.basename(temp_file_path),
            size=os.path.getsize(temp_file_path),
            user=user
        )
        await sync_to_async(file_instance.save)()

        folderToSplit = f'uploads/{DATE}/{userName}/{
            os.path.basename(temp_file_path).split(".")[0]}'
        os.makedirs(folderToSplit, exist_ok=True)

        chunksPaths = await sync_to_async(split_file)(temp_file_path, chunk_size=CHUNK_SIZE, folder=folderToSplit)

        # Upload chunks in batches
        try:
            chunk_tasks = []
            for i, chunk in enumerate(chunksPaths):
                chunk_tasks.append(uploadChunk(
                    chunk, userName, file_instance.id))
                if len(chunk_tasks) == 5 or i == len(chunksPaths) - 1:  # Change batch size here
                    # Wait for the current batch to finish
                    await asyncio.gather(*chunk_tasks)
                    chunk_tasks = []  # Reset the task list for the next batch
        except Exception as e:
            file_instance.uploadedSuccessfully = False
            await sync_to_async(file_instance.save)()
            return str(file_instance.id)
        # Clean up the temporary file
        deleteFolder(f'temp/{user.username}')
        deleteFolder(folderToSplit)
        deleteFolder(f'uploads/{DATE}/{userName}/{file_instance.id}')
        file_instance.uploading = False
        await sync_to_async(file_instance.save)()
        return str(file_instance.id)

    async def uploadChunk(filePath: str, userName: str, file_id):
        random_string = await getRandomString(10)
        fileCompressedName = f'{random_string}.zip'
        print('Chunk uploading')
        await sync_to_async(compress_file)(file_to_compress=filePath, folder=f'uploads/{DATE}/{userName}/{file_id}', output_zip=fileCompressedName)
        fileCompressedPath = f'uploads/{DATE}/{userName}/{
            file_id}/{fileCompressedName}'
        chunk_id = await _upload_file_support(bot, fileCompressedPath)

        chunk_instance = Chunk(
            file_id=file_id
        )
        chunk_instance.set_message(chunk_id)
        await sync_to_async(chunk_instance.save)()
        print('Chunk uploaded')

    def compress_file(file_to_compress, output_zip, folder):
        if not os.path.exists(folder):
            os.makedirs(folder)
        with zipfile.ZipFile(os.path.join(folder, output_zip), 'w') as zipf:
            zipf.write(file_to_compress, os.path.basename(
                file_to_compress), compress_type=zipfile.ZIP_DEFLATED)

    async def _upload_file_support(bot, file_path):
        with open(file_path, 'rb') as file:
            response = await bot.send_document(
                chat_id=CHAT_ID,
                document=InputFile(file),
                read_timeout=10 * 5,
                write_timeout=20 * 5,
                connect_timeout=10 * 5,
                pool_timeout=5 * 5
            )
            return response.document.file_id

    time1 = time.time()
    file_id = asyncio.run(uploadFile(temp_file_path, userName))
    deleteFolder(f'temp/{userName}')
    print(f"Time taken: {round(time.time()-time1, 2)}s")
    file = File.objects.get(id=file_id)
    if file.uploadedSuccessfully:
        message = f"{file.file_name} uploaded successfully"
    else:
        message = f"Error uploading {file.file_name}"
    notification = Notificacions(
        user=file.user,
        message=message,
        file=file
    )
    notification.save()
