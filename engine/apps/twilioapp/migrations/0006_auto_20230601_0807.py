# Generated by Django 3.2.18 on 2023-06-01 08:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('twilioapp', '0005_twilioaccount_twiliophonecallsender_twiliosmssender_twilioverificationsender'),
    ]

    operations = [
        migrations.AlterField(
            model_name='twiliophonecall',
            name='sid',
            field=models.CharField(blank=True, db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='twiliosms',
            name='sid',
            field=models.CharField(blank=True, db_index=True, max_length=50),
        ),
    ]
