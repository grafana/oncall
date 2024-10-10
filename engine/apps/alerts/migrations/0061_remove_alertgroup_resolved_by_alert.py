from django.db import migrations


class Migration(migrations.Migration):
    """
    Fake migration to drop column and remove constraint
    """
    dependencies = [
        ('alerts', '0060_relatedincident'),
    ]

    operations = [
        migrations.RunSQL(
            sql=migrations.RunSQL.noop,
            reverse_sql=migrations.RunSQL.noop,
            state_operations=[
                migrations.RemoveField(
                    model_name='alertgroup',
                    name='resolved_by_alert',
                ),
            ]
        ),
        migrations.RunSQL(
            sql="ALTER TABLE alerts_alertgroup DROP FOREIGN KEY alerts_alertgroup_resolved_by_alert_id_bbdf0a83_fk_alerts_al;",
            reverse_sql=migrations.RunSQL.noop
        )
    ]