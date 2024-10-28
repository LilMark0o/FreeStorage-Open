from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from upload.models import File
import uuid


class SharedFile(models.Model):
    file = models.ForeignKey(
        File, on_delete=models.CASCADE, related_name='shared_files')
    # The user sharing the file
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    share_link = models.CharField(
        max_length=255, default=uuid.uuid4, unique=True)  # Unique link
    expiration_date = models.DateTimeField(
        null=True, blank=True)  # Time-based expiration
    max_downloads = models.IntegerField(
        null=True, blank=True)  # Usage-based expiration
    limitless_downloads = models.BooleanField(default=False)
    # Track current number of downloads
    downloads = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    hard_turn_off = models.BooleanField(default=False)

    def is_valid(self):
        """Check if the share link is still valid based on expiration or downloads."""
        if self.hard_turn_off:
            return False
        if self.expiration_date and timezone.now() > self.expiration_date:
            return False
        if (self.max_downloads and self.downloads >= self.max_downloads) and (not self.limitless_downloads):
            return False
        return True

    def increment_download(self):
        """Increase the download count."""
        self.downloads += 1
        self.save()

    def __str__(self):
        return f'SharedFile({self.file.file_name}) - {self.share_link}'
