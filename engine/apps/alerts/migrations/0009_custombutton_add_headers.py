# Generated by Django 3.2.16 on 2023-01-20 16:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0008_alter_alertgrouplogrecord_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='custombutton',
            name='headers',
            field=models.TextField(default=None, null=True),
        ),
    ]
