# Generated by Django 3.2.19 on 2023-06-16 15:10

from django.db import migrations, models
from django.db.models import Count

from common.database import get_random_readonly_database_key_if_present_otherwise_default
import django_migration_linter as linter


def fix_duplicate_order_user_notification_policy(apps, schema_editor):
    UserNotificationPolicy = apps.get_model('base', 'UserNotificationPolicy')

    # it should be safe to use a readonly database because duplicates are pretty infrequent
    db = get_random_readonly_database_key_if_present_otherwise_default()

    # find all (user_id, important, order) tuples that have more than one entry (meaning duplicates)
    items_with_duplicate_orders = UserNotificationPolicy.objects.using(db).values(
        "user_id", "important", "order"
    ).annotate(count=Count("order")).order_by().filter(count__gt=1)  # use order_by() to reset any existing ordering

    # make sure we don't fix the same (user_id, important) pair more than once
    values_to_fix = set((item["user_id"], item["important"]) for item in items_with_duplicate_orders)

    for user_id, important in values_to_fix:
        policies = UserNotificationPolicy.objects.filter(user_id=user_id, important=important).order_by("order", "id")
        # assign correct sequential order for each policy starting from 0
        for idx, policy in enumerate(policies):
            policy.order = idx
        UserNotificationPolicy.objects.bulk_update(policies, fields=["order"])


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_delete_organizationlogrecord'),
    ]

    operations = [
        linter.IgnoreMigration(),  # adding a unique constraint after fixing duplicates should be fine
        migrations.AlterField(
            model_name='usernotificationpolicy',
            name='order',
            field=models.PositiveIntegerField(db_index=True, editable=False, null=True),
        ),
        migrations.RunPython(fix_duplicate_order_user_notification_policy, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='usernotificationpolicy',
            constraint=models.UniqueConstraint(fields=('user_id', 'important', 'order'), name='unique_user_notification_policy_order'),
        ),
    ]
