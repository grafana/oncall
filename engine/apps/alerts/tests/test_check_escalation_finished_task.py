import pytest
from django.utils import timezone

from apps.alerts.models import AlertReceiveChannel
from apps.alerts.tasks import check_escalation_finished_task


@pytest.mark.django_db
def test_check_escalation_finished_task(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )
    alert_group = make_alert_group(alert_receive_channel)

    now = timezone.now()

    # we don't have escalation finish time, seems we cannot calculate it due escalation chain snapshot has uncalculated
    # steps or does not exist, no exception is raised
    check_escalation_finished_task()

    # it's acceptable time for finish escalation, because we have tolerance time 5 min from now, no exception is raised
    alert_group.estimate_escalation_finish_time = now
    alert_group.save()
    check_escalation_finished_task()

    # it is acceptable time for finish escalation, so no exception is raised
    alert_group.estimate_escalation_finish_time = now + timezone.timedelta(minutes=10)
    alert_group.save()
    check_escalation_finished_task()

    # escalation is not finished yet and passed more than 5 minutes after estimate time, exception is raised
    alert_group.estimate_escalation_finish_time = now - timezone.timedelta(minutes=10)
    alert_group.save()
    with pytest.raises(Exception):
        check_escalation_finished_task()

    # escalation is finished and we don't care anymore about its finish time, so no exception is raised
    alert_group.is_escalation_finished = True
    alert_group.save()
    check_escalation_finished_task()
