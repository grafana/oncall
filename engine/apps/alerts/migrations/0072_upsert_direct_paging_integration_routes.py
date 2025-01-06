# Generated by Django 4.2.17 on 2024-12-20 14:19

import logging

from django.db import migrations
from django.db.models import Count

logger = logging.getLogger(__name__)


def upsert_direct_paging_integration_routes(apps, schema_editor):
    AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")
    ChannelFilter = apps.get_model("alerts", "ChannelFilter")

    DIRECT_PAGING_INTEGRATION_TYPE = "direct_paging"
    IMPORTANT_FILTERING_TERM = "{{ payload.oncall.important }}"

    # Fetch all direct paging integrations
    logger.info("Fetching direct paging integrations which have not had their routes updated.")

    # Ignore updating Direct Paging integrations that have > 1 route, as this means that users have
    # gone ahead and created their own routes. We don't want to overwrite these.
    unedited_direct_paging_integrations = (
        AlertReceiveChannel.objects
        .filter(integration=DIRECT_PAGING_INTEGRATION_TYPE)
        .annotate(num_routes=Count("channel_filters"))
        .filter(num_routes=1)
    )

    integration_count = unedited_direct_paging_integrations.count()
    if integration_count == 0:
        logger.info("No integrations found which meet this criteria. No routes will be upserted.")
        return

    logger.info(f"Found {integration_count} direct paging integrations that meet this criteria.")

    # Direct Paging Integrations are currently created with a single default route (order=0)
    # see AlertReceiveChannelManager.create_missing_direct_paging_integrations
    #
    # we first need to update this route to be order=1, and then we will subsequently bulk-create the
    # non-default route (order=0) which will have a filtering term set
    routes = ChannelFilter.objects.filter(
        alert_receive_channel__in=unedited_direct_paging_integrations,
        is_default=True,
        order=0,
    )
    route_ids = list(routes.values_list("pk", flat=True))

    logger.info(
        f"Swapping the order=0 value to order=1 for {len(route_ids)} Direct Paging Integrations default routes"
    )

    updated_rows = ChannelFilter.objects.filter(pk__in=route_ids).update(order=1)
    logger.info(f"Swapped order=0 to order=1 for {updated_rows} Direct Paging Integrations default routes")

    # Bulk create the new non-default routes
    logger.info(f"Creating new non-default routes for {integration_count} Direct Paging Integrations")
    created_objs = ChannelFilter.objects.bulk_create(
        [
            ChannelFilter(
                alert_receive_channel=integration,
                filtering_term=IMPORTANT_FILTERING_TERM,
                filtering_term_type=1,  # 1 = ChannelFilter.FILTERING_TERM_TYPE_JINJA2
                is_default=False,
                order=0,
            ) for integration in unedited_direct_paging_integrations
        ],
        batch_size=5000,
    )
    logger.info(f"Created {len(created_objs)} new non-default routes for Direct Paging Integrations")

    logger.info("Migration for direct paging integration routes completed.")


class Migration(migrations.Migration):

    dependencies = [
        ("alerts", "0071_migrate_labels"),
    ]

    operations = [
        migrations.RunPython(upsert_direct_paging_integration_routes, migrations.RunPython.noop),
    ]
