# Generated by Django 4.2.7 on 2023-11-22 06:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('webhooks', '0011_auto_20230920_1813'),
        ('user_management', '0017_alter_organization_maintenance_author'),
        ('labels', '0003_alertreceivechannelassociatedlabel_inherit'),
    ]

    operations = [
        migrations.CreateModel(
            name='WebhookAssociatedLabel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='labels.labelkeycache')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='webhook_labels', to='user_management.organization')),
                ('value', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='labels.labelvaluecache')),
                ('webhook', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='labels', to='webhooks.webhook')),
            ],
            options={
                'unique_together': {('key_id', 'value_id', 'webhook_id')},
            },
        ),
    ]
