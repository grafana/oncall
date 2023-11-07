from celery import uuid as celery_uuid
from django.core.management import BaseCommand
from django.utils import timezone

from apps.alerts.models import AlertGroup
from apps.alerts.tasks import escalate_alert_group, unsilence_task


class Command(BaseCommand):
    """
    Start escalation for alert groups from the point it was stopped with optionally start unsilence task for silenced
    alert groups.

    Usage example:
    `python manage.py continue_escalation -ppk "ppk1" "ppk2"` - continue escalation for alert groups with these
    public pks
    `python manage.py continue_escalation -id 1 2 -uns` - continue escalation for alert groups with these ids and
    schedule unsilence task for silenced alert groups
    """

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)

        group.add_argument(
            "-id", "--alert_group_ids", type=int, nargs="+", help="Alert group IDs to restart escalation for."
        )
        group.add_argument(
            "-ppk", "--alert_group_ppk", type=str, nargs="+", help="Alert group public pks to restart escalation for."
        )
        group.add_argument(
            "--all", action="store_true", help="Restart escalation for all alert groups with unfinished escalation."
        )
        parser.add_argument(
            "-uns", "--unsilence_task", action="store_true", help="Restart unsilence task for selected alert groups."
        )
        parser.add_argument(  # used for cases with migrated organizations to actualize data in escalation snapshot
            "-rebuild",
            "--rebuild_escalation_snapshot",
            action="store_true",
            help="Rebuild escalation snapshot for selected alert groups.",
        )

    def handle(self, *args, **options):
        alert_group_ids = options["alert_group_ids"]
        alert_group_ppk = options["alert_group_ppk"]
        restart_all = options["all"]
        restart_unsilence_task = options["unsilence_task"]
        rebuild_escalation_snapshot = options["rebuild_escalation_snapshot"]

        if restart_all:
            self.stdout.write("Processing restart escalation for all active alert groups...")
            alert_groups = AlertGroup.objects.filter_active()
        elif alert_group_ids:
            self.stdout.write(f"Processing restart escalation for alert groups with ids: {alert_group_ids}...")
            alert_groups = AlertGroup.objects.filter(
                pk__in=alert_group_ids,
                raw_escalation_snapshot__isnull=False,
            )
        else:
            self.stdout.write(f"Processing restart escalation for alert groups with ppks: {alert_group_ppk}...")
            alert_groups = AlertGroup.objects.filter(
                public_primary_key__in=alert_group_ppk,
                raw_escalation_snapshot__isnull=False,
            )

        if not alert_groups:
            self.stdout.write("No escalations to restart.")
            return

        tasks = []
        alert_groups_to_update = []
        now = timezone.now()

        for alert_group in alert_groups:
            # rebuild escalation snapshot with keeping information about current escalation step
            # this is used for migrated organizations to actualize data in escalation snapshot
            if rebuild_escalation_snapshot:
                self._write_stdout_log(
                    restart_all,
                    f"rebuild escalation snapshot for alert group (id: {alert_group.id}, ppk: "
                    f"{alert_group.public_primary_key})",
                )
                original_escalation_snapshot = alert_group.raw_escalation_snapshot
                new_escalation_snapshot = alert_group.build_raw_escalation_snapshot()
                snapshot_fields_to_copy = ["last_active_escalation_policy_order", "next_step_eta", "pause_escalation"]
                for field in snapshot_fields_to_copy:
                    new_escalation_snapshot[field] = original_escalation_snapshot[field]
                alert_group.raw_escalation_snapshot = new_escalation_snapshot

            task_id = celery_uuid()
            # if incident was silenced, start unsilence_task
            if alert_group.is_silenced_for_period:
                if not restart_unsilence_task:
                    self._write_stdout_log(
                        restart_all,
                        f"alert group (id: {alert_group.id}, ppk: {alert_group.public_primary_key}) is silenced, skip",
                    )
                    continue
                self._write_stdout_log(
                    restart_all,
                    f"alert group (id: {alert_group.id}, ppk: {alert_group.public_primary_key}) is silenced, "
                    f"scheduling unsilence task",
                )
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
            elif alert_group.escalation_snapshot:
                self._write_stdout_log(
                    restart_all,
                    f"Run escalation for alert group (id: {alert_group.id}, ppk: {alert_group.public_primary_key})",
                )
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
            else:
                self._write_stdout_log(
                    restart_all,
                    f"alert group (id: {alert_group.id}, ppk: {alert_group.public_primary_key}) doesn't have escalation"
                    f" snapshot, skip",
                )

        AlertGroup.objects.bulk_update(
            alert_groups_to_update,
            ["active_escalation_id", "unsilence_task_uuid", "raw_escalation_snapshot"],
            batch_size=5000,
        )

        for task in tasks:
            task.apply_async()

        restarted_alert_group_ids = ", ".join(
            f"(id: {str(alert_group.pk)}, ppk: {alert_group.public_primary_key})" for alert_group in alert_groups
        )
        self.stdout.write(f"Escalations restarted for alert groups: {restarted_alert_group_ids}")

    def _write_stdout_log(self, restart_all, text):
        """Write log if restart escalation not for all alert groups"""
        if not restart_all:
            self.stdout.write(text)
