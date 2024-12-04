# Generated by Django 4.2.11 on 2024-12-04 04:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0071_migrate_labels'),
        ('user_management', '0029_remove_organization_general_log_channel_id_db'),
        ('labels', '0006_remove_alertreceivechannelassociatedlabel_inheritable_state'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metaname', models.CharField(max_length=200)),
                ('spec', models.JSONField()),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='custom_fields', to='user_management.organization')),
            ],
        ),
        migrations.CreateModel(
            name='IntegrationHasCustomField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template', models.TextField(default=None, null=True)),
                ('static_value', models.CharField(default=None, max_length=200, null=True)),
                ('custom_field', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='labels.customfield')),
                ('integration', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='alerts.alertreceivechannel')),
            ],
            options={
                'unique_together': {('integration', 'custom_field')},
            },
        ),
    ]
