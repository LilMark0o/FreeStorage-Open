# Generated by Django 5.1.1 on 2024-10-21 15:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_userprofile_verification_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='sizePerFile',
            field=models.IntegerField(default=26214400),
        ),
    ]
