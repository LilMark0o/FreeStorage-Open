from django.db import models
from django.contrib.auth.models import User
import os
from cryptography.fernet import Fernet

key = os.getenv('ENCRYPTION_KEY')
cipher_suite = Fernet(key.encode())  # Convert the string back to bytes


class File(models.Model):
    file_name = models.CharField(max_length=255)
    date = models.DateField(auto_now_add=True)
    size = models.IntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uploading = models.BooleanField(default=True)
    uploadedSuccessfully = models.BooleanField(default=True)
    tags = models.ManyToManyField('Tags', blank=True, related_name='files')

    def __str__(self):
        return self.file_name


class Tags(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tag = models.CharField(max_length=255)

    def __str__(self):
        return self.tag


class Chunk(models.Model):
    # Only store the encrypted message
    encrypted_data = models.BinaryField(default=b'')
    file = models.ForeignKey(
        'File', on_delete=models.CASCADE, related_name='chunks')

    def __str__(self):
        return f'Chunk {self.id} of File {self.file.file_name}'

    def save(self, *args, **kwargs):
        # Ensure the encrypted_data is already set (this will be done before saving the object)
        super().save(*args, **kwargs)

    def set_message(self, message):
        # Encrypt the message and store it in the encrypted_data field
        self.encrypted_data = cipher_suite.encrypt(message.encode())

    def get_decrypted_message(self):
        # Decrypt the stored encrypted_data and return the original message
        return cipher_suite.decrypt(self.encrypted_data).decode()


class Notificacions(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    date = models.DateField(auto_now_add=True)
    shown = models.BooleanField(default=False)
    file = models.ForeignKey(
        File, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.message
