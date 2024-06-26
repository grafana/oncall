# Generated by Django 4.2.11 on 2024-06-19 21:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('phone_notifications', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BannedPhoneNumber',
            fields=[
                ('phone_number', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('reason', models.TextField(default=None, null=True)),
                ('users', models.JSONField(default=None, null=True)),
            ],
        ),
    ]
