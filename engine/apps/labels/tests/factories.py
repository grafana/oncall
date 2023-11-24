import factory

from apps.labels.models import (
    AlertGroupAssociatedLabel,
    AlertReceiveChannelAssociatedLabel,
    LabelKeyCache,
    LabelValueCache,
    WebhookAssociatedLabel,
)
from common.utils import UniqueFaker


class LabelKeyFactory(factory.DjangoModelFactory):
    id = UniqueFaker("pystr", max_chars=36)
    name = UniqueFaker("sentence", nb_words=3)

    class Meta:
        model = LabelKeyCache


class LabelValueFactory(factory.DjangoModelFactory):
    id = UniqueFaker("pystr", max_chars=36)
    name = UniqueFaker("sentence", nb_words=3)

    class Meta:
        model = LabelValueCache


class AlertReceiveChannelAssociatedLabelFactory(factory.DjangoModelFactory):
    class Meta:
        model = AlertReceiveChannelAssociatedLabel


class AlertGroupAssociatedLabelFactory(factory.DjangoModelFactory):
    class Meta:
        model = AlertGroupAssociatedLabel


class WebhookAssociatedLabelFactory(factory.DjangoModelFactory):
    class Meta:
        model = WebhookAssociatedLabel
