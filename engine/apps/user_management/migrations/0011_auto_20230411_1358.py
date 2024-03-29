# Generated by Django 3.2.18 on 2023-04-11 13:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0010_team_is_sharing_resources_to_all'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='gcom_org_contract_type',
            field=models.CharField(default=None, max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='gcom_org_irm_sku_subscription_start_date',
            field=models.DateTimeField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='gcom_org_oldest_admin_with_billing_privileges_user_id',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
