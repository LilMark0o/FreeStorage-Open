from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from kombu import Exchange, Queue

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'free_storage.settings')

# Create a Celery instance
app = Celery('free_storage')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically discover tasks from all registered apps
app.autodiscover_tasks()

# Update Celery configuration for task queues
app.conf.update(
    broker_pool_limit=3,  # Limit connections to broker
    broker_heartbeat=30,  # 1 minute
    broker_connection_timeout=30,  # 1 minute
    result_backend='rpc://',
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # Disable prefetching
    task_default_rate_limit='10/s',
)

# Define task queues for uploads and downloads
app.conf.task_queues = (
    Queue('upload_queue', Exchange('upload_queue'), routing_key='upload'),
    Queue('download_queue', Exchange('download_queue'), routing_key='download'),
)

# Define routes for the tasks
app.conf.task_routes = {
    'free_storage.tasks.bigUploadTask': {'queue': 'upload_queue'},
    'free_storage.tasks.bigDownloadTask': {'queue': 'download_queue'},
}


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
