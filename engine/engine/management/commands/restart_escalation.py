from celery import uuid as celery_uuid
from django.core.management import BaseCommand
from django.db.models import Q
from django.utils import timezone

from apps.alerts.models import AlertGroup, AlertReceiveChannel
from apps.alerts.tasks import escalate_alert_group, unsilence_task


class Command(BaseCommand):
    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)

        group.add_argument("--alert_group_ids", type=int, nargs="+", help="Alert group IDs to restart escalation for.")
        group.add_argument(
            "--all", action="store_true", help="Restart escalation for all alert groups with unfinished escalation."
        )

    def handle(self, *args, **options):
        alert_group_ids = options["alert_group_ids"]
        restart_all = options["all"]

        if restart_all:
            alert_groups = AlertGroup.all_objects.filter(
                ~Q(channel__integration=AlertReceiveChannel.INTEGRATION_MAINTENANCE),
                ~Q(silenced=True, silenced_until__isnull=True),  # filter silenced forever alert_groups
                Q(Q(is_escalation_finished=False) | Q(silenced_until__isnull=False)),
                resolved=False,
                acknowledged=False,
                root_alert_group=None,
            )
        else:
            alert_groups = AlertGroup.all_objects.filter(
                pk__in=alert_group_ids,
            )

        if not alert_groups:
            self.stdout.write("No escalations to restart.")
            return

        tasks = []
        alert_groups_to_update = []
        now = timezone.now()

        for alert_group in alert_groups:
            task_id = celery_uuid()
            # if incident was silenced, start unsilence_task
            if alert_group.is_silenced_for_period:
                alert_group.unsilence_task_uuid = task_id

                escalation_start_time = max(now, alert_group.silenced_until)
                alert_groups_to_update.append(alert_group)

                tasks.append(
                    unsilence_task.signature(
                        args=(alert_group.pk,),
                        immutable=True,
                        task_id=task_id,
                        eta=escalation_start_time,
                    )
                )
            # otherwise start escalate_alert_group task
            else:
                if alert_group.escalation_snapshot:
                    alert_group.active_escalation_id = task_id
                    alert_groups_to_update.append(alert_group)

                    tasks.append(
                        escalate_alert_group.signature(
                            args=(alert_group.pk,),
                            immutable=True,
                            task_id=task_id,
                            eta=alert_group.next_step_eta,
                        )
                    )

        AlertGroup.all_objects.bulk_update(
            alert_groups_to_update,
            ["active_escalation_id", "unsilence_task_uuid"],
            batch_size=5000,
        )

        for task in tasks:
            task.apply_async()

        restarted_alert_group_ids = ", ".join(str(alert_group.pk) for alert_group in alert_groups)
        self.stdout.write("Escalations restarted for alert groups: {}".format(restarted_alert_group_ids))
