# Generated by Django 3.2.19 on 2023-05-25 15:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('twilioapp', '0004_twiliophonecall_twiliosms'),
    ]

    operations = [
        migrations.CreateModel(
            name='TwilioAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('account_sid', models.CharField(max_length=64, unique=True)),
                ('auth_token', models.CharField(default=None, max_length=64, null=True)),
                ('api_key_sid', models.CharField(default=None, max_length=64, null=True)),
                ('api_key_secret', models.CharField(default=None, max_length=64, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TwilioVerificationSender',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Default', max_length=100)),
                ('country_code', models.CharField(default=None, max_length=16, null=True)),
                ('verify_service_sid', models.CharField(max_length=64)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='twilioapp_twilioverificationsender_account', to='twilioapp.twilioaccount')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TwilioSmsSender',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Default', max_length=100)),
                ('country_code', models.CharField(default=None, max_length=16, null=True)),
                ('sender', models.CharField(max_length=16)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='twilioapp_twiliosmssender_account', to='twilioapp.twilioaccount')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TwilioPhoneCallSender',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Default', max_length=100)),
                ('country_code', models.CharField(default=None, max_length=16, null=True)),
                ('number', models.CharField(max_length=16)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='twilioapp_twiliophonecallsender_account', to='twilioapp.twilioaccount')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
