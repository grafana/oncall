# Generated by Django 3.2.20 on 2023-09-12 15:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user_management', '0014_auto_20230728_0802'),
        ('alerts', '0032_remove_alertgroup_slack_message_state'),
    ]

    operations = [
        migrations.CreateModel(
            name='Label',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key_id', models.CharField(max_length=20)),
                ('value_id', models.CharField(max_length=20)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='labels', to='user_management.organization')),
            ],
            options={
                'unique_together': {('key_id', 'value_id', 'organization')},
            },
        ),
        migrations.CreateModel(
            name='AlertReceiveChannelAssociatedLabel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alert_receive_channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='alerts.alertreceivechannel')),
                ('label', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='labels.label')),
            ],
        ),
    ]
