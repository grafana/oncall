import factory

from apps.heartbeat.models import IntegrationHeartBeat


class IntegrationHeartBeatFactory(factory.DjangoModelFactory):
    class Meta:
        model = IntegrationHeartBeat
