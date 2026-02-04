# Generated migration for Zoom template fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0075_alter_alertgrouplogrecord_action_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='alertreceivechannel',
            name='zoom_title_template',
            field=models.TextField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='alertreceivechannel',
            name='zoom_message_template',
            field=models.TextField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='alertreceivechannel',
            name='zoom_image_url_template',
            field=models.TextField(default=None, null=True),
        ),
    ]
