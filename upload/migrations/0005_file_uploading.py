# Generated by Django 5.1.1 on 2024-10-01 19:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0004_remove_file_size2'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='uploading',
            field=models.BooleanField(default=True),
        ),
    ]
