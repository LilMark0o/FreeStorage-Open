# Generated by Django 5.1.1 on 2024-10-10 22:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_userprofile_authenticated'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='verification_code',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]