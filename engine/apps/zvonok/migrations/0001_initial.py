# Generated by Django 3.2.19 on 2023-07-01 12:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('phone_notifications', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZvonokPhoneCall',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.PositiveSmallIntegerField(blank=True, choices=[(10, 'attempts_exc'), (20, 'compl_finished'), (30, 'compl_nofinished'), (40, 'deleted'), (50, 'duration_error'), (60, 'expires'), (70, 'novalid_button'), (80, 'no_provider'), (90, 'interrupted'), (100, 'in_process'), (110, 'pincode_nook'), (130, 'synth_error'), (140, 'user')], null=True)),
                ('call_id', models.CharField(blank=True, max_length=50)),
                ('campaign_id', models.CharField(max_length=50)),
                ('phone_call_record', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='zvonok_zvonokphonecall_related', related_query_name='zvonok_zvonokphonecalls', to='phone_notifications.phonecallrecord')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
