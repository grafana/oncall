from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Fake migration to drop column and remove constraint
    """
    dependencies = [
        ('alerts', '0060_relatedincident'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alertgroup',
            name='resolved_by_alert',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='resolved_alert_groups', to='alerts.alert'),
        ),
        migrations.RunSQL(
            sql="ALTER TABLE alerts_alertgroup DROP FOREIGN KEY alerts_alertgroup_resolved_by_alert_id_bbdf0a83_fk_alerts_al;",
            reverse_sql=migrations.RunSQL.noop
        )
    ]