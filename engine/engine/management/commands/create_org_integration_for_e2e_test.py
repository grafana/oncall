from django.core.management import BaseCommand
from django.db.models.signals import post_save
from django.urls import reverse

from apps.alerts.models import AlertReceiveChannel, listen_for_alertreceivechannel_model_save
from apps.alerts.tests.factories import AlertReceiveChannelFactory
from apps.user_management.tests.factories import OrganizationFactory


class Command(BaseCommand):
    def handle(self, *args, **options):
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
