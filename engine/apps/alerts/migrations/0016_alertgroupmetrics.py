# Generated by Django 3.2.19 on 2023-05-16 15:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0015_auto_20230508_1641'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlertGroupMetrics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('response_time', models.DurationField(default=None, null=True)),
                ('alert_group', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='metrics', to='alerts.alertgroup')),
            ],
        ),
    ]
