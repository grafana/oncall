from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("alerts", "0026_auto_20230719_1010"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name="alertreceivechannel",
                    name="restricted_at",
                ),
            ],
            database_operations=[],
        )
    ]
