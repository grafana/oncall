# Generated by Django 4.2.15 on 2024-10-18 16:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0023_organization_is_grafana_irm_enabled'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='direct_paging_use_important_policy',
            field=models.BooleanField(default=False, null=True),
        ),
    ]
