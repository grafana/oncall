# Generated by Django 3.2.18 on 2023-04-11 19:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0010_fix_polymorphic_delete_related'),
    ]

    operations = [
        migrations.AddField(
            model_name='oncallschedule',
            name='cached_ical_final_schedule',
            field=models.TextField(default=None, null=True),
        ),
    ]
