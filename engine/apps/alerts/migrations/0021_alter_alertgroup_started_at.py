# Generated by Django 3.2.20 on 2023-07-13 06:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0020_auto_20230711_1532'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alertgroup',
            name='started_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
    ]
