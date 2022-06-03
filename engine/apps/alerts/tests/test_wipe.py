import pytest

from apps.alerts.tasks.wipe import wipe


@pytest.mark.django_db
def test_wipe_alert_group(
    make_organization_and_user,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, user = make_organization_and_user()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    wipe(alert_group.pk, user.pk)

    alert_group.refresh_from_db()
    assert alert_group.wiped_at is not None
    assert alert_group.wiped_by == user
