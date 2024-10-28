from django.contrib import admin
from .models import File, Chunk, Tags, Notificacions

admin.site.register(File)
admin.site.register(Chunk)
admin.site.register(Tags)
admin.site.register(Notificacions)
