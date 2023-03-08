from django.db import migrations, models
import django.db.models.deletion


def delete_user_duplicate_mobileappauthtokens(apps, _):
    MobileAppAuthToken = apps.get_model('mobile_app', 'MobileAppAuthToken')

    # start w/ the oldest mobile app auth tokens (ORDER BY id ASC)
    # and if we find any newer tokens, delete the earlier ones (ie. `row` variable)
    for row in MobileAppAuthToken.objects.all().order_by('id'):
        if MobileAppAuthToken.objects.filter(user_id=row.user_id).count() > 1:
            row.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0008_organization_is_grafana_incident_enabled'),
        ('mobile_app', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(delete_user_duplicate_mobileappauthtokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='mobileappauthtoken',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='user_management.user'),
        ),
    ]
