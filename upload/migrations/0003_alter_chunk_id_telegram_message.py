# Generated by Django 5.1.1 on 2024-09-26 18:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chunk',
            name='id_telegram_message',
            field=models.CharField(max_length=150),
        ),
    ]