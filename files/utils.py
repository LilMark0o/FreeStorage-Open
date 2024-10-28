# free_storage/upload/celery.py
from __future__ import absolute_import, unicode_literals
import datetime
import time
from celery import shared_task
from free_storage.celery import app
from dotenv import load_dotenv
from upload.models import Chunk, File  # Import the Chunk and File models
import os
import shutil
import zipfile
import telegram
import requests
from telegram import InputFile
from random import choice
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User  # Import the User model

from telegram.request import HTTPXRequest


@shared_task(soft_time_limit=60*60, time_limit=60*60, queue='download_queue')
def bigDownloadTask(fileId, userName, folderPath=f'downloads/{str(datetime.datetime.now().date())}'):
    request = HTTPXRequest(connect_timeout=60*60*24,
                           read_timeout=60*60*24, write_timeout=60*60*24,
                           pool_timeout=60*60*24,
                           # Increase write_timeout
                           connection_pool_size=50)  # Increase write_timeout

    load_dotenv()
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    bot = telegram.Bot(token=TOKEN, request=request)

    def recreate_folder(folder_path):
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            print(f"Folder deleted: {folder_path}")

        os.makedirs(folder_path)
        print(f"Folder created: {folder_path}")

    async def getRandomString(length: int):
        alphanumeric = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        return ''.join(choice(alphanumeric) for _ in range(length))

    async def _download_file_support(bot, file_id, download_path, folderPath):
        retry = 2
        i = 0
        while i < retry:
            try:
                file = await bot.get_file(file_id)
                file_path = file.file_path
                file_url = file_path
                if '.zip' not in file_url:
                    download_path += '.zip'
                response = requests.get(file_url, stream=True)
                response.raw.decode_content = False  # Disables encoding checks
                if response.status_code == 200:
                    # Save the file
                    with open(download_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                else:
                    raise Exception(
                        f'Failed to download file: {response.status_code} {response.reason}')
                with zipfile.ZipFile(download_path, 'r') as zipf:
                    zipf.extractall(folderPath)
                os.remove(download_path)
                return None

            except Exception as e:
                print(f'Error: {e}, retrying...')

            i += 1
        return None

    async def decompress_file(zip_file, extract_to):
        """
        Decompresses a ZIP archive.

        :param zip_file: Path to the ZIP file to be decompressed.
        :param extract_to: Directory where the contents should be extracted.
        """
        with zipfile.ZipFile(zip_file, 'r') as zipf:
            zipf.extractall(extract_to)
        os.remove(zip_file)

    def de_split_file(folder, output_file=None) -> str:
        chunk_files = sorted(os.listdir(folder))
        base_name = chunk_files[0].split('_')[0]
        file_ext = "."+chunk_files[0].split('.')[1]

        if output_file is None:
            output_file = f"{base_name}{file_ext}"

        with open(folder + "/" + output_file, 'wb') as output_f:
            for chunk in chunk_files:
                if chunk.startswith(base_name) and chunk.endswith(file_ext):
                    chunk_path = os.path.join(folder, chunk)
                    with open(chunk_path, 'rb') as chunk_f:
                        output_f.write(chunk_f.read())
        for chunk in chunk_files:
            os.remove(folder + "/" + chunk)
        return folder+'/'+output_file

    async def downloadFile(fileId: str, userName: str, folderPath: str = './downloads'):
        file = await sync_to_async(File.objects.get)(id=fileId)
        chunks = await sync_to_async(list)(Chunk.objects.filter(file=file))
        if len(chunks) == 0:
            raise Exception("No chunks")
        folderPath = f'{folderPath}/{userName}/{fileId}'
        recreate_folder(folderPath)
        chunk_tasks = []
        for i, chunk in enumerate(chunks):
            chunkID = chunk.get_decrypted_message()
            random_string = await getRandomString(10)  # Await the coroutine

            chunk_tasks.append(_download_file_support(bot, chunkID, f'''{
                               folderPath}/your_downloaded_file_{random_string}''', folderPath))
            if len(chunk_tasks) == 5 or i == len(chunks) - 1:  # Procesa en bloques de 5
                # Espera que el batch actual termine
                await asyncio.gather(*chunk_tasks)
                chunk_tasks = []  # Reinicia la lista de tareas para el siguiente batch
        filePathReconstructed = de_split_file(folderPath)
        return filePathReconstructed

    import asyncio
    time1 = time.time()
    print("let's start")
    filePath = asyncio.run(
        downloadFile(fileId, userName, folderPath))
    print(f"Time taken: {round(time.time()-time1, 2)}s")
    return filePath
