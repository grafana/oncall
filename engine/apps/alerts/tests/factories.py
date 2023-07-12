import factory

from apps.alerts.models import (
    Alert,
    AlertGroup,
    AlertGroupLogRecord,
    AlertReceiveChannel,
    ChannelFilter,
    CustomButton,
    EscalationChain,
    EscalationPolicy,
    Invitation,
    ResolutionNote,
    ResolutionNoteSlackMessage,
)
from common.utils import UniqueFaker


class AlertReceiveChannelFactory(factory.DjangoModelFactory):
    # integration = AlertReceiveChannel.INTEGRATION_GRAFANA
    verbal_name = factory.Faker("sentence", nb_words=2)

    class Meta:
        model = AlertReceiveChannel


class ChannelFilterFactory(factory.DjangoModelFactory):
    class Meta:
        model = ChannelFilter


class EscalationChainFactory(factory.DjangoModelFactory):
    name = UniqueFaker("word")

    class Meta:
        model = EscalationChain


class EscalationPolicyFactory(factory.DjangoModelFactory):
    class Meta:
        model = EscalationPolicy


class AlertFactory(factory.DjangoModelFactory):
    class Meta:
        model = Alert


class AlertGroupFactory(factory.DjangoModelFactory):
    class Meta:
        model = AlertGroup


class AlertGroupLogRecordFactory(factory.DjangoModelFactory):
    class Meta:
        model = AlertGroupLogRecord


class ResolutionNoteFactory(factory.DjangoModelFactory):
    message_text = factory.Faker("sentence", nb_words=5)

    class Meta:
        model = ResolutionNote


class ResolutionNoteSlackMessageFactory(factory.DjangoModelFactory):
    class Meta:
        model = ResolutionNoteSlackMessage


class CustomActionFactory(factory.DjangoModelFactory):
    webhook = factory.Faker("url")
    name = UniqueFaker("word")

    class Meta:
        model = CustomButton


class InvitationFactory(factory.DjangoModelFactory):
    class Meta:
        model = Invitation
