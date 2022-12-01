# Generated by Django 3.2.16 on 2022-12-01 08:09

import pytz
from django.db import migrations

from common.timezones import is_valid_timezone


def fix_bad_timezone_values(model):
    def _fix_bad_timezone_values(apps, _schema_editor):
        """
            https://docs.djangoproject.com/en/4.1/topics/migrations/#data-migrations

            We can't import the model directly as it may be a newer
            version than this migration expects. We use the historical version.
        """
        Model = apps.get_model('schedules', model)
        for obj in Model.objects.all():
            if obj.time_zone and not is_valid_timezone(obj.time_zone):
                obj.time_zone = pytz.UTC
                obj.save()

    return _fix_bad_timezone_values


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0007_customoncallshift_updated_shift'),
    ]

    operations = [
        migrations.RunPython(fix_bad_timezone_values('CustomOnCallShift')),
        migrations.RunPython(fix_bad_timezone_values('OnCallScheduleCalendar')),
        migrations.RunPython(fix_bad_timezone_values('OnCallScheduleWeb')),
    ]
