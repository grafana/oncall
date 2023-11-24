from celery import uuid as celery_uuid
from django.core.management import BaseCommand

from apps.alerts.models import AlertGroup
from apps.alerts.tasks import acknowledge_reminder_task
from apps.user_management.models import Organization


class Command(BaseCommand):
    """
    Restart acknowledge_reminder_task for organization. Used for migrated organizations.

    Usage example:
    `python manage.py restart_acknowledge_reminder -ppk "organization ppk"` - restart task for alert groups from
    organizations with this public pk
    """

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)

        group.add_argument(
            "-ppk", "--organization_ppk", type=str, help="Organization public pks to restart reminder for."
        )

    def handle(self, *args, **options):
        organization_ppk = options["organization_ppk"]
        organization = Organization.objects.get(public_primary_key=organization_ppk)
        self.stdout.write(
            f"Processing restart acknowledge reminder for alert groups from organization "
            f"(id: {organization.id}, ppk: {organization.public_primary_key})..."
        )
        if organization.acknowledge_remind_timeout == 0:
            self.stdout.write("Organization doesn't have acknowledge reminder setting set")
            return

        alert_groups = AlertGroup.objects.filter(
            acknowledged=True,
            resolved=False,
            silenced=False,
            maintenance_uuid__isnull=True,
            root_alert_group=None,
            channel__organization=organization,
        )
        if not alert_groups:
            self.stdout.write("No affected alert groups.")
            return

        self.stdout.write(f"Affected alert groups count: {alert_groups.count()}.")

        tasks = []
        alert_groups_to_update = []

        for alert_group in alert_groups:
            task_id = celery_uuid()
            countdown = Organization.ACKNOWLEDGE_REMIND_DELAY[organization.acknowledge_remind_timeout]
            alert_group.last_unique_unacknowledge_process_id = task_id
            alert_groups_to_update.append(alert_group)
            tasks.append(
                acknowledge_reminder_task.signature(
                    args=(alert_group.pk, task_id), immutable=True, task_id=task_id, countdown=countdown
                )
            )

        AlertGroup.objects.bulk_update(
            alert_groups_to_update,
            ["last_unique_unacknowledge_process_id"],
            batch_size=5000,
        )

        for task in tasks:
            task.apply_async()

        self.stdout.write("Acknowledge reminder has been restarted for affected alert groups")
