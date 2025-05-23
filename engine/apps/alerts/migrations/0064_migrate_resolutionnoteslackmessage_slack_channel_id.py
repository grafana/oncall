# Generated by Django 4.2.16 on 2024-11-01 10:58
import logging

from django.db import migrations
import django_migration_linter as linter

logger = logging.getLogger(__name__)


def populate_slack_channel(apps, schema_editor):
    ResolutionNoteSlackMessage = apps.get_model("alerts", "ResolutionNoteSlackMessage")
    SlackChannel = apps.get_model("slack", "SlackChannel")
    AlertGroup = apps.get_model("alerts", "AlertGroup")
    AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")
    Organization = apps.get_model("user_management", "Organization")

    logger.info("Starting migration to populate slack_channel field.")

    # NOTE: the following raw SQL only works on mysql, fall back to the less-efficient (but working) ORM method
    # for non-mysql databases
    #
    # see the following references for more information:
    # https://github.com/grafana/oncall/issues/5244#issuecomment-2493688544
    # https://github.com/grafana/oncall/pull/5233/files#diff-4ee42d7e773e6116d7c1d0280d2dbb053422ea55bfa5802a1f26ffbf23a28867
    if schema_editor.connection.vendor == "mysql":
        sql = f"""
        UPDATE {ResolutionNoteSlackMessage._meta.db_table} AS rsm
        JOIN {AlertGroup._meta.db_table} AS ag ON ag.id = rsm.alert_group_id
        JOIN {AlertReceiveChannel._meta.db_table} AS arc ON arc.id = ag.channel_id
        JOIN {Organization._meta.db_table} AS org ON org.id = arc.organization_id
        JOIN {SlackChannel._meta.db_table} AS sc ON sc.slack_id = rsm._slack_channel_id
                            AND sc.slack_team_identity_id = org.slack_team_identity_id
        SET rsm.slack_channel_id = sc.id
        WHERE rsm._slack_channel_id IS NOT NULL
        AND org.slack_team_identity_id IS NOT NULL;
        """

        with schema_editor.connection.cursor() as cursor:
            cursor.execute(sql)
            updated_rows = cursor.rowcount  # Number of rows updated

        logger.info(f"Bulk updated {updated_rows} ResolutionNoteSlackMessage records with their Slack channel.")
        logger.info("Finished migration to populate slack_channel field.")
    else:
        queryset = ResolutionNoteSlackMessage.objects.filter(
            _slack_channel_id__isnull=False,
            alert_group__channel__organization__slack_team_identity__isnull=False,
        )
        total_resolution_notes = queryset.count()
        updated_resolution_notes = 0
        missing_resolution_notes = 0
        resolution_notes_to_update = []

        logger.info(f"Total resolution note slack messages to process: {total_resolution_notes}")

        for resolution_note in queryset:
            slack_id = resolution_note._slack_channel_id
            slack_team_identity = resolution_note.alert_group.channel.organization.slack_team_identity

            try:
                slack_channel = SlackChannel.objects.get(slack_id=slack_id, slack_team_identity=slack_team_identity)
                resolution_note.slack_channel = slack_channel
                resolution_notes_to_update.append(resolution_note)

                updated_resolution_notes += 1
                logger.info(
                    f"ResolutionNoteSlackMessage {resolution_note.id} updated with SlackChannel {slack_channel.id} "
                    f"(slack_id: {slack_id})."
                )
            except SlackChannel.DoesNotExist:
                missing_resolution_notes += 1
                logger.warning(
                    f"SlackChannel with slack_id {slack_id} and slack_team_identity {slack_team_identity} "
                    f"does not exist for ResolutionNoteSlackMessage {resolution_note.id}."
                )

        if resolution_notes_to_update:
            ResolutionNoteSlackMessage.objects.bulk_update(resolution_notes_to_update, ["slack_channel"])
            logger.info(
                f"Bulk updated {len(resolution_notes_to_update)} ResolutionNoteSlackMessage with their Slack channel."
            )

        logger.info(
            f"Finished migration. Total resolution note slack messages processed: {total_resolution_notes}. "
            f"Resolution note slack messages updated: {updated_resolution_notes}. "
            f"Missing SlackChannels: {missing_resolution_notes}."
        )


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0063_migrate_channelfilter_slack_channel_id'),
    ]

    operations = [
        # simply setting this new field is okay, we are not deleting the value of channel
        # therefore, no need to revert it
        linter.IgnoreMigration(),
        migrations.RunPython(populate_slack_channel, migrations.RunPython.noop),
    ]
