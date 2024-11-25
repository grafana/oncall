import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.models import Max, Min

from apps.slack.models import SlackChannel, SlackMessage
from apps.user_management.models import Organization


class Command(BaseCommand):
    help = "Batch updates SlackMessage.channel_id in chunks to avoid locking the table."

    def handle(self, *args, **options):
        start_time = time.time()
        self.stdout.write("Starting batch update of SlackMessage.channel_id...")

        # Step 1: Determine the range of 'created_at' values to update
        qs = SlackMessage.objects.filter(
            _channel_id__isnull=False,  # old column
            organization__isnull=False,
            channel_id__isnull=True,  # new column
        )

        total_records = qs.count()
        if total_records == 0:
            self.stdout.write("No records to update.")
            return

        min_created_at = qs.aggregate(Min("created_at"))["created_at__min"]
        max_created_at = qs.aggregate(Max("created_at"))["created_at__max"]

        self.stdout.write(f"Total records to update: {total_records}")
        self.stdout.write(f"Created_at range: {min_created_at} to {max_created_at}")

        # Step 2: Define batch interval
        BATCH_INTERVAL = timedelta(days=1)
        self.stdout.write(f"Batch interval: {BATCH_INTERVAL}")

        # Step 3: Generate time ranges
        batch_starts = []
        current_start = min_created_at
        while current_start <= max_created_at:
            batch_starts.append(current_start)
            current_start += BATCH_INTERVAL

        total_batches = len(batch_starts)
        self.stdout.write(f"Total batches: {total_batches}")

        records_updated = 0

        # Step 4: Process updates in time-based batches
        for batch_number, batch_start in enumerate(batch_starts, start=1):
            batch_end = batch_start + BATCH_INTERVAL
            # Adjust the last batch's end time
            if batch_end > max_created_at:
                batch_end = max_created_at + timedelta(seconds=1)  # Include the max_created_at

            self.stdout.write(
                f"Batch {batch_number}/{total_batches}: Processing records from {batch_start} to {batch_end}"
            )

            update_query = f"""
                UPDATE
                    {SlackMessage._meta.db_table} AS sm
                INNER JOIN {Organization._meta.db_table} AS org
                    ON org.id = sm.organization_id
                INNER JOIN {SlackChannel._meta.db_table} AS sc
                    ON sc.slack_id = sm._channel_id
                    AND sc.slack_team_identity_id = org.slack_team_identity_id
                SET
                    sm.channel_id = sc.id
                WHERE
                    sm._channel_id IS NOT NULL
                    AND sm.organization_id IS NOT NULL
                    AND sm.channel_id IS NULL
                    AND sm.created_at >= %s AND sm.created_at < %s
            """
            params = [batch_start, batch_end]

            try:
                # Execute the update
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute(update_query, params)
                        batch_records_updated = cursor.rowcount
                        records_updated += batch_records_updated

                self.stdout.write(f"Batch {batch_number}/{total_batches}: Updated {batch_records_updated} records")
            except Exception as e:
                self.stderr.write(f"Error updating batch {batch_number}: {e}")
                # Optionally, decide whether to continue or abort
                continue

        end_time = time.time()
        total_time = end_time - start_time
        self.stdout.write(f"Batch update completed successfully. Total records updated: {records_updated}")
        self.stdout.write(f"Total time taken: {total_time:.2f} seconds")
