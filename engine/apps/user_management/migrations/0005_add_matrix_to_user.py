from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_management', '0004_auto_20221025_0316'),
        ('matrix', '0001_squashed_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='matrix_user_identity',
            field=models.ForeignKey(default=None, null=True, on_delete=models.deletion.PROTECT, related_name='matrix', to='matrix.matrixuseridentity')
        )
    ]
