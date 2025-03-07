from datetime import timedelta
from unittest.mock import patch

import pytest
from celery import uuid as celery_uuid
from django.core.cache import cache
from django.utils import timezone

from apps.alerts.constants import ActionSource
from apps.alerts.models import AlertGroup, AlertGroupLogRecord
from apps.alerts.tasks import acknowledge_reminder_task
from apps.alerts.tasks.acknowledge_reminder import send_post_ack_reminder_message_signal, unacknowledge_timeout_task
from apps.user_management.models import Organization

TASK_ID = "TASK_ID"


def _parametrize_or(best, worst):
    """
    Utility method to parametrize tests with multiple OR conditions. best = best case, when all the conditions in
    the OR statement are True. worst = worst case, when all the conditions in the OR statement are False.
    """
    assert len(best) == len(worst)
    return [(*best[:i], worst[i], *best[i + 1 :]) for i in range(len(best))]


@pytest.fixture
def ack_reminder_test_setup(
    make_organization,
    make_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    def _ack_reminder_test_setup(
        task_id=TASK_ID,
        acknowledged=True,
        acknowledged_by=AlertGroup.USER,
        resolved=False,
        set_root_alert_group=False,
        acknowledge_remind_timeout=Organization.ACKNOWLEDGE_REMIND_1H,
        unacknowledge_timeout=Organization.UNACKNOWLEDGE_TIMEOUT_5MIN,
        acknowledged_by_confirmed=None,
    ):
        organization = make_organization(
            acknowledge_remind_timeout=acknowledge_remind_timeout, unacknowledge_timeout=unacknowledge_timeout
        )
        user = make_user(organization=organization)
        alert_receive_channel = make_alert_receive_channel(organization)
        root_alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)
        alert_group = make_alert_group(
            alert_receive_channel,
            acknowledged=acknowledged,
            acknowledged_by=acknowledged_by,
            acknowledged_by_user=user,
            resolved=resolved,
            root_alert_group_id=root_alert_group.id if set_root_alert_group else None,
        )

        alert_group.last_unique_unacknowledge_process_id = task_id
        alert_group.acknowledged_by_confirmed = acknowledged_by_confirmed
        alert_group.save(update_fields=["last_unique_unacknowledge_process_id", "acknowledged_by_confirmed"])

        return organization, alert_group, user

    return _ack_reminder_test_setup


@pytest.mark.django_db
def test_acknowledge_by_user_invokes_start_ack_reminder(ack_reminder_test_setup):
    organization, alert_group, user = ack_reminder_test_setup(acknowledged=False)

    with patch.object(alert_group, "start_ack_reminder_if_needed") as mock_start_ack_reminder:
        alert_group.acknowledge_by_user_or_backsync(user, ActionSource.SLACK)
        mock_start_ack_reminder.assert_called_once_with()


@pytest.mark.django_db
def test_bulk_acknowledge_invokes_start_ack_reminder(ack_reminder_test_setup):
    organization, alert_group, user = ack_reminder_test_setup(acknowledged=False)

    with patch.object(AlertGroup, "start_ack_reminder_if_needed") as mock_start_ack_reminder:
        AlertGroup.bulk_acknowledge(user, AlertGroup.objects.filter(pk=alert_group.pk))
        mock_start_ack_reminder.assert_called_once_with()


@pytest.mark.django_db
def test_start_ack_reminder_invokes_acknowledge_reminder_task(ack_reminder_test_setup):
    organization, alert_group, user = ack_reminder_test_setup()

    # make sure celery_uuid returns a string to be passed to the task
    assert type(celery_uuid()) == str

    with patch.object(acknowledge_reminder_task, "apply_async") as mock_acknowledge_reminder_task:
        with patch("apps.alerts.models.alert_group.celery_uuid", return_value=TASK_ID):
            alert_group.start_ack_reminder_if_needed()
            mock_acknowledge_reminder_task.assert_called_once_with(
                (alert_group.pk, TASK_ID),
                countdown=Organization.ACKNOWLEDGE_REMIND_DELAY[organization.acknowledge_remind_timeout],
            )


@pytest.mark.parametrize(
    "set_root_alert_group,acknowledge_remind_timeout",
    _parametrize_or(
        best=(False, Organization.ACKNOWLEDGE_REMIND_1H),
        worst=(True, Organization.ACKNOWLEDGE_REMIND_NEVER),
    ),
)
@pytest.mark.django_db
def test_ack_reminder_skip(ack_reminder_test_setup, set_root_alert_group, acknowledge_remind_timeout):
    organization, alert_group, user = ack_reminder_test_setup(
        acknowledge_remind_timeout=acknowledge_remind_timeout, set_root_alert_group=set_root_alert_group
    )

    with patch.object(acknowledge_reminder_task, "apply_async") as mock_acknowledge_reminder_task:
        alert_group.start_ack_reminder_if_needed()
        mock_acknowledge_reminder_task.assert_not_called()


@pytest.mark.parametrize(
    "task_id,acknowledged,acknowledged_by,resolved,set_root_alert_group,acknowledge_remind_timeout",
    _parametrize_or(
        best=(TASK_ID, True, AlertGroup.USER, False, False, Organization.ACKNOWLEDGE_REMIND_1H),
        worst=(None, False, AlertGroup.SOURCE, True, True, Organization.ACKNOWLEDGE_REMIND_NEVER),
    ),
)
@patch.object(unacknowledge_timeout_task, "apply_async")
@patch.object(acknowledge_reminder_task, "apply_async")
@pytest.mark.django_db
def test_acknowledge_reminder_task_skip(
    mock_acknowledge_reminder_task,
    mock_unacknowledge_timeout_task,
    ack_reminder_test_setup,
    task_id,
    acknowledged,
    acknowledged_by,
    resolved,
    set_root_alert_group,
    acknowledge_remind_timeout,
):
    organization, alert_group, user = ack_reminder_test_setup(
        task_id=task_id,
        acknowledged=acknowledged,
        acknowledged_by=acknowledged_by,
        resolved=resolved,
        set_root_alert_group=set_root_alert_group,
        acknowledge_remind_timeout=acknowledge_remind_timeout,
    )
    acknowledge_reminder_task(alert_group.pk, TASK_ID)

    mock_unacknowledge_timeout_task.assert_not_called()
    mock_acknowledge_reminder_task.assert_not_called()

    assert not alert_group.log_records.exists()


@patch.object(unacknowledge_timeout_task, "apply_async")
@patch.object(acknowledge_reminder_task, "apply_async")
@patch.object(send_post_ack_reminder_message_signal, "delay")
@pytest.mark.django_db
def test_acknowledge_reminder_task_reschedules_itself_and_sends_signal(
    mock_send_post_ack_reminder_message_signal,
    mock_acknowledge_reminder_task,
    mock_unacknowledge_timeout_task,
    ack_reminder_test_setup,
    django_capture_on_commit_callbacks,
):
    organization, alert_group, user = ack_reminder_test_setup(
        unacknowledge_timeout=Organization.UNACKNOWLEDGE_TIMEOUT_NEVER
    )
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        acknowledge_reminder_task(alert_group.pk, TASK_ID)

    mock_unacknowledge_timeout_task.assert_not_called()
    mock_acknowledge_reminder_task.assert_called_once_with(
        (alert_group.pk, TASK_ID),
        countdown=Organization.ACKNOWLEDGE_REMIND_DELAY[organization.acknowledge_remind_timeout],
    )

    log_record = alert_group.log_records.get()
    assert log_record.type == AlertGroupLogRecord.TYPE_ACK_REMINDER_TRIGGERED
    assert log_record.author == alert_group.acknowledged_by_user

    # send_post_ack_reminder_message_signal task is queued after commit
    assert len(callbacks) == 1
    mock_send_post_ack_reminder_message_signal.assert_called_once_with(log_record.id)


@patch.object(unacknowledge_timeout_task, "apply_async")
@patch.object(acknowledge_reminder_task, "apply_async")
@pytest.mark.django_db
def test_acknowledge_reminder_task_invokes_unacknowledge_timeout_task(
    mock_acknowledge_reminder_task, mock_unacknowledge_timeout_task, ack_reminder_test_setup
):
    organization, alert_group, user = ack_reminder_test_setup(
        unacknowledge_timeout=Organization.UNACKNOWLEDGE_TIMEOUT_5MIN
    )
    acknowledge_reminder_task(alert_group.pk, TASK_ID)

    mock_acknowledge_reminder_task.assert_not_called()
    mock_unacknowledge_timeout_task.assert_called_with(
        (alert_group.pk, TASK_ID),
        countdown=Organization.UNACKNOWLEDGE_TIMEOUT_DELAY[organization.unacknowledge_timeout],
    )

    alert_group.refresh_from_db()
    assert alert_group.acknowledged_by_confirmed is None

    log_record = alert_group.log_records.get()
    assert log_record.type == AlertGroupLogRecord.TYPE_ACK_REMINDER_TRIGGERED
    assert log_record.author == alert_group.acknowledged_by_user


@pytest.mark.parametrize(
    "task_id,acknowledged,acknowledged_by,resolved,set_root_alert_group,acknowledge_remind_timeout,unacknowledge_timeout",
    _parametrize_or(
        best=(
            TASK_ID,
            True,
            AlertGroup.USER,
            False,
            False,
            Organization.ACKNOWLEDGE_REMIND_1H,
            Organization.UNACKNOWLEDGE_TIMEOUT_5MIN,
        ),
        worst=(
            None,
            False,
            AlertGroup.SOURCE,
            True,
            True,
            Organization.ACKNOWLEDGE_REMIND_NEVER,
            Organization.UNACKNOWLEDGE_TIMEOUT_NEVER,
        ),
    ),
)
@patch.object(unacknowledge_timeout_task, "apply_async")
@patch.object(acknowledge_reminder_task, "apply_async")
@pytest.mark.django_db
def test_unacknowledge_timeout_task_skip(
    mock_acknowledge_reminder_task,
    mock_unacknowledge_timeout_task,
    ack_reminder_test_setup,
    task_id,
    acknowledged,
    acknowledged_by,
    resolved,
    set_root_alert_group,
    acknowledge_remind_timeout,
    unacknowledge_timeout,
):
    organization, alert_group, user = ack_reminder_test_setup(
        task_id=task_id,
        acknowledged=acknowledged,
        acknowledged_by=acknowledged_by,
        resolved=resolved,
        set_root_alert_group=set_root_alert_group,
        acknowledge_remind_timeout=acknowledge_remind_timeout,
        unacknowledge_timeout=unacknowledge_timeout,
    )
    unacknowledge_timeout_task(alert_group.pk, TASK_ID)

    mock_unacknowledge_timeout_task.assert_not_called()
    mock_acknowledge_reminder_task.assert_not_called()

    assert not alert_group.log_records.exists()


@patch.object(AlertGroup, "start_escalation_if_needed")
@patch.object(AlertGroup, "unacknowledge")
@patch.object(unacknowledge_timeout_task, "apply_async")
@patch.object(acknowledge_reminder_task, "apply_async")
@pytest.mark.django_db
def test_unacknowledge_timeout_task_unacknowledge(
    mock_acknowledge_reminder_task,
    mock_unacknowledge_timeout_task,
    mock_unacknowledge,
    mock_start_escalation_if_needed,
    ack_reminder_test_setup,
):
    organization, alert_group, user = ack_reminder_test_setup()
    unacknowledge_timeout_task(alert_group.pk, TASK_ID)

    mock_unacknowledge_timeout_task.assert_not_called()
    mock_acknowledge_reminder_task.assert_not_called()

    log_record = alert_group.log_records.get()
    assert log_record.type == AlertGroupLogRecord.TYPE_AUTO_UN_ACK
    assert log_record.author == alert_group.acknowledged_by_user

    mock_unacknowledge.assert_called_once_with()
    mock_start_escalation_if_needed.assert_called_once_with()


@patch.object(unacknowledge_timeout_task, "apply_async")
@patch.object(acknowledge_reminder_task, "apply_async")
@pytest.mark.django_db
def test_unacknowledge_timeout_task_no_unacknowledge(
    mock_acknowledge_reminder_task, mock_unacknowledge_timeout_task, ack_reminder_test_setup
):
    organization, alert_group, user = ack_reminder_test_setup(acknowledged_by_confirmed=timezone.now())
    unacknowledge_timeout_task(alert_group.pk, TASK_ID)

    mock_unacknowledge_timeout_task.assert_not_called()
    mock_acknowledge_reminder_task.assert_called_once_with(
        (alert_group.pk, TASK_ID),
        countdown=Organization.ACKNOWLEDGE_REMIND_DELAY[organization.acknowledge_remind_timeout]
        - Organization.UNACKNOWLEDGE_TIMEOUT_DELAY[organization.unacknowledge_timeout],
    )

    assert not alert_group.log_records.exists()


@patch.object(acknowledge_reminder_task, "apply_async")
@patch.object(unacknowledge_timeout_task, "apply_async")
@pytest.mark.django_db
def test_ack_reminder_skip_deleted_org(
    mock_acknowledge_reminder_task,
    mock_unacknowledge_timeout_task,
    ack_reminder_test_setup,
):
    organization, alert_group, user = ack_reminder_test_setup()
    organization.deleted_at = timezone.now()
    organization.save()

    acknowledge_reminder_task(alert_group.pk, TASK_ID)

    mock_unacknowledge_timeout_task.assert_not_called()
    mock_acknowledge_reminder_task.assert_not_called()

    assert not alert_group.log_records.exists()


@patch.object(acknowledge_reminder_task, "apply_async")
@patch.object(unacknowledge_timeout_task, "apply_async")
@pytest.mark.django_db
def test_unacknowledge_timeout_task_skip_deleted_org(
    mock_acknowledge_reminder_task,
    mock_unacknowledge_timeout_task,
    ack_reminder_test_setup,
):
    organization, alert_group, user = ack_reminder_test_setup()
    organization.deleted_at = timezone.now()
    organization.save()

    unacknowledge_timeout_task(alert_group.pk, TASK_ID)

    mock_unacknowledge_timeout_task.assert_not_called()
    mock_acknowledge_reminder_task.assert_not_called()

    assert not alert_group.log_records.exists()


@patch.object(acknowledge_reminder_task, "apply_async")
@patch.object(unacknowledge_timeout_task, "apply_async")
@pytest.mark.django_db
def test_ack_reminder_cancel_too_old(
    mock_acknowledge_reminder_task,
    mock_unacknowledge_timeout_task,
    ack_reminder_test_setup,
    settings,
):
    organization, alert_group, user = ack_reminder_test_setup(
        unacknowledge_timeout=Organization.UNACKNOWLEDGE_TIMEOUT_NEVER
    )
    alert_group.started_at = timezone.now() - timedelta(days=settings.ACKNOWLEDGE_REMINDER_TASK_EXPIRY_DAYS + 1)
    alert_group.save()

    acknowledge_reminder_task(alert_group.pk, TASK_ID)

    mock_unacknowledge_timeout_task.assert_not_called()
    mock_acknowledge_reminder_task.assert_not_called()

    assert not alert_group.log_records.exists()


@pytest.mark.django_db
def test_acknowledge_reminder_skip_doubled_notification(
    ack_reminder_test_setup,
    django_capture_on_commit_callbacks,
    caplog,
):
    organization, alert_group, user = ack_reminder_test_setup(
        unacknowledge_timeout=Organization.UNACKNOWLEDGE_TIMEOUT_NEVER
    )
    expected_log_text = f"Acknowledge reminder for alert_group {alert_group.id} has already been sent recently."

    # check task lock cache doesn't exist
    lock_id = f"acknowledge-reminder-lock-{alert_group.id}"
    assert cache.get(lock_id) is None

    with patch.object(acknowledge_reminder_task, "apply_async") as mock_acknowledge_reminder_task:
        with patch.object(send_post_ack_reminder_message_signal, "delay") as mock_send_signal:
            with django_capture_on_commit_callbacks(execute=True):
                acknowledge_reminder_task(alert_group.pk, TASK_ID)

            log_record = alert_group.log_records.get()
            assert log_record.type == AlertGroupLogRecord.TYPE_ACK_REMINDER_TRIGGERED
            mock_send_signal.assert_called_once_with(log_record.id)
            mock_acknowledge_reminder_task.assert_called_once()

    # check task lock cache exists
    assert cache.get(lock_id) == TASK_ID

    assert expected_log_text not in caplog.text

    # acknowledge_reminder_task doesn't proceed the second time if it has been called recently
    with patch.object(acknowledge_reminder_task, "apply_async") as mock_acknowledge_reminder_task:
        with patch.object(send_post_ack_reminder_message_signal, "delay") as mock_send_signal:
            with django_capture_on_commit_callbacks(execute=True):
                acknowledge_reminder_task(alert_group.pk, TASK_ID)

            assert alert_group.log_records.count() == 1
            mock_send_signal.assert_not_called()
            mock_acknowledge_reminder_task.assert_not_called()

    assert expected_log_text in caplog.text
