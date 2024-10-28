from django.contrib import admin

# Register your models here.

from .models import SharedFile

admin.site.register(SharedFile)
