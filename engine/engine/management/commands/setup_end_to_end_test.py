from django.core.management import BaseCommand
from django.db.models.signals import post_save
from django.urls import reverse

from apps.alerts.models import Alert, AlertGroup, AlertReceiveChannel, listen_for_alertreceivechannel_model_save
from apps.alerts.tests.factories import AlertReceiveChannelFactory
from apps.user_management.tests.factories import OrganizationFactory


class Command(BaseCommand):
    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--bootstrap_integration",
            action="store_true",
            help="Create random formatted webhook integration",
        )

        group.add_argument(
            "--return_results_for_test_id",
            type=str,
            help="Count alert groups with specific text in the title and their alerts",
        )

    def handle(self, *args, **options):
        if options["bootstrap_integration"]:
            organization = OrganizationFactory()

            def _make_alert_receive_channel(organization, **kwargs):
                if "integration" not in kwargs:
                    kwargs["integration"] = "formatted_webhook"
                post_save.disconnect(listen_for_alertreceivechannel_model_save, sender=AlertReceiveChannel)
                alert_receive_channel = AlertReceiveChannelFactory(organization=organization, **kwargs)
                post_save.connect(listen_for_alertreceivechannel_model_save, sender=AlertReceiveChannel)
                return alert_receive_channel

            integration = _make_alert_receive_channel(
                organization, integration=AlertReceiveChannel.INTEGRATION_FORMATTED_WEBHOOK
            )
            url = reverse(
                "integrations:universal",
                kwargs={
                    "integration_type": AlertReceiveChannel.INTEGRATION_FORMATTED_WEBHOOK,
                    "alert_channel_key": integration.token,
                },
            )
            return url
        elif test_id := options["return_results_for_test_id"]:
            alert_groups_pks = list(AlertGroup.all_objects.filter(web_title_cache=test_id).values_list("id", flat=True))
            alert_groups_count = len(alert_groups_pks)
            alerts_count = Alert.objects.filter(group_id__in=alert_groups_pks).count()
            return f"{alert_groups_count}, {alerts_count}"
