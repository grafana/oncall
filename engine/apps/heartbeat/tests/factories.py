import factory

from apps.heartbeat.models import IntegrationHeartBeat


class IntegrationHeartBeatFactory(factory.DjangoModelFactory):
    actual_check_up_task_id = "none"

    class Meta:
        model = IntegrationHeartBeat
