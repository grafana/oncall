# Generated by Django 3.2.20 on 2023-09-13 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slack', '0003_delete_slackactionrecord'),
    ]

    operations = [
        migrations.AlterField(
            model_name='slackteamidentity',
            name='access_token',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='slackteamidentity',
            name='bot_access_token',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
    ]
