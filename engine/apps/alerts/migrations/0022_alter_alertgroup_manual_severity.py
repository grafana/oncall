# Generated by Django 3.2.20 on 2023-07-18 06:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0021_alter_alertgroup_started_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alertgroup',
            name='manual_severity',
            field=models.IntegerField(choices=[(0, 'high'), (1, 'low'), (2, 'none')], default=2, null=True),
        ),
    ]
