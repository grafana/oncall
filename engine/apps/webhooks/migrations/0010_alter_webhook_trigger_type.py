# Generated by Django 3.2.20 on 2023-08-14 22:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webhooks', '0009_alter_webhook_authorization_header'),
    ]

    operations = [
        migrations.AlterField(
            model_name='webhook',
            name='trigger_type',
            field=models.IntegerField(choices=[(0, 'Escalation step'), (1, 'Alert Group Created'), (2, 'Acknowledged'), (3, 'Resolved'), (4, 'Silenced'), (5, 'Unsilenced'), (6, 'Unresolved'), (7, 'Unacknowledged')], default=0, null=True),
        ),
    ]
