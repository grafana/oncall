# Generated by Django 3.2.19 on 2023-06-08 10:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobile_app', '0007_alter_mobileappusersettings_info_notifications_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='mobileappusersettings',
            name='locale',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
