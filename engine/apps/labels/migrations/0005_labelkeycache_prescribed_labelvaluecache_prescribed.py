# Generated by Django 4.2.7 on 2024-02-07 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('labels', '0004_webhookassociatedlabel'),
    ]

    operations = [
        migrations.AddField(
            model_name='labelkeycache',
            name='prescribed',
            field=models.BooleanField(default=False, null=True),
        ),
        migrations.AddField(
            model_name='labelvaluecache',
            name='prescribed',
            field=models.BooleanField(default=False, null=True),
        ),
    ]
