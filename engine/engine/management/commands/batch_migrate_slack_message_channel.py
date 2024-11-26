import time
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from apps.slack.models import SlackMessage, SlackChannel
from apps.user_management.models import Organization


class Command(BaseCommand):
    help = "Batch updates SlackMessage.channel_id in chunks to avoid locking the table."

    def handle(self, *args, **options):
        start_time = time.time()
        self.stdout.write("Starting batch update of SlackMessage.channel_id...")

        # Step 1: Determine the queryset to update
        # qs is ordered by id to ensure consistent batching
        # since id is indexed, this ordering operation "should" be more efficient (as opposed to say created_at
        # which we don't have an index on)
        qs = SlackMessage.objects.filter(
            _channel_id__isnull=False,  # old column
            organization__isnull=False,
            channel_id__isnull=True,    # new column
        ).order_by('id')

        total_records = qs.count()
        if total_records == 0:
            self.stdout.write("No records to update.")
            return

        self.stdout.write(f"Total records to update: {total_records}")

        # some considerations here..
        #
        # Large IN clauses can be inefficient. Keep BATCH_SIZE reasonable (e.g., 1000)
        # Fetching large batches of IDs consumes memory. With a BATCH_SIZE of 1000, this "should" be manageable
        #
        # references
        # https://stackoverflow.com/a/5919165
        BATCH_SIZE = 1000

        total_batches = (total_records + BATCH_SIZE - 1) // BATCH_SIZE
        self.stdout.write(f"Batch size: {BATCH_SIZE}")
        self.stdout.write(f"Total batches: {total_batches}")

        records_updated = 0
        batch_number = 1

        # Process updates in batches
        while True:
            # Get the next batch of IDs
            batch_qs = qs[:BATCH_SIZE]

            # collect the IDs to be updated
            batch_ids = list(batch_qs.values_list('id', flat=True))

            if not batch_ids:
                break  # No more records to process

            placeholders = ', '.join(['%s'] * len(batch_ids))
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
                    sm.id IN ({placeholders})
            """
            params = batch_ids

            try:
                # Execute the update
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute(update_query, params)
                        batch_records_updated = cursor.rowcount
                        records_updated += batch_records_updated

                self.stdout.write(
                    f"Batch {batch_number}/{total_batches}: Updated {batch_records_updated} records"
                )
            except Exception as e:
                self.stderr.write(
                    f"Error updating batch {batch_number}: {e}"
                )
                # Optionally, decide whether to continue or abort
                continue

            # Remove processed records from queryset for next batch
            qs = qs.exclude(id__in=batch_ids)

            batch_number += 1

        end_time = time.time()
        total_time = end_time - start_time
        self.stdout.write(
            f"Batch update completed successfully. Total records updated: {records_updated}"
        )
        self.stdout.write(f"Total time taken: {total_time:.2f} seconds")
