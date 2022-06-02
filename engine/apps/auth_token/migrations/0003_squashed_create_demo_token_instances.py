# Generated by Django 3.2.5 on 2021-08-04 13:02

import sys
from django.db import migrations

from apps.auth_token import constants
from apps.auth_token import crypto
from apps.public_api import constants as public_api_constants


def create_demo_token_instances(apps, schema_editor):
    if not (len(sys.argv) > 1 and sys.argv[1] == 'test'):
        User = apps.get_model('user_management', 'User')
        Organization = apps.get_model('user_management', 'Organization')
        ApiAuthToken = apps.get_model('auth_token', 'ApiAuthToken')

        organization = Organization.objects.get(public_primary_key=public_api_constants.DEMO_ORGANIZATION_ID)
        user = User.objects.get(public_primary_key=public_api_constants.DEMO_USER_ID)

        token_string = crypto.generate_token_string()
        digest = crypto.hash_token_string(token_string)

        ApiAuthToken.objects.get_or_create(
            name=public_api_constants.DEMO_AUTH_TOKEN,
            user=user,
            organization=organization,
                defaults=dict(token_key=token_string[:constants.TOKEN_KEY_LENGTH], digest=digest)
        )


class Migration(migrations.Migration):

    dependencies = [
        ('auth_token', '0002_squashed_initial'),
        ('user_management', '0002_squashed_create_demo_token_instances')
    ]

    operations = [
        migrations.RunPython(create_demo_token_instances, migrations.RunPython.noop)
    ]
