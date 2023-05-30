import json

import pytest

from apps.alerts.incident_appearance.renderers.slack_renderer import AlertGroupSlackRenderer
from apps.alerts.models import AlertGroup


@pytest.mark.django_db
def test_slack_renderer_acknowledge_button(make_organization, make_alert_receive_channel, make_alert_group, make_alert):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={})

    elements = AlertGroupSlackRenderer(alert_group).render_alert_group_attachments()[0]["blocks"][0]["elements"]

    ack_button = elements[0]
    assert ack_button["text"]["text"] == "Acknowledge"
    assert json.loads(ack_button["value"]) == {"organization_id": organization.pk, "alert_group_pk": alert_group.pk}


@pytest.mark.django_db
def test_slack_renderer_unacknowledge_button(
    make_organization, make_alert_receive_channel, make_alert_group, make_alert
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, acknowledged=True)
    make_alert(alert_group=alert_group, raw_request_data={})

    elements = AlertGroupSlackRenderer(alert_group).render_alert_group_attachments()[0]["blocks"][0]["elements"]

    ack_button = elements[0]
    assert ack_button["text"]["text"] == "Unacknowledge"
    assert json.loads(ack_button["value"]) == {"organization_id": organization.pk, "alert_group_pk": alert_group.pk}


@pytest.mark.django_db
def test_slack_renderer_resolve_button(make_organization, make_alert_receive_channel, make_alert_group, make_alert):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={})

    elements = AlertGroupSlackRenderer(alert_group).render_alert_group_attachments()[0]["blocks"][0]["elements"]

    ack_button = elements[1]
    assert ack_button["text"]["text"] == "Resolve"
    assert json.loads(ack_button["value"]) == {"organization_id": organization.pk, "alert_group_pk": alert_group.pk}


@pytest.mark.django_db
def test_slack_renderer_unresolve_button(make_organization, make_alert_receive_channel, make_alert_group, make_alert):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, resolved=True)
    make_alert(alert_group=alert_group, raw_request_data={})

    elements = AlertGroupSlackRenderer(alert_group).render_alert_group_attachments()[0]["blocks"][0]["elements"]

    ack_button = elements[0]
    assert ack_button["text"]["text"] == "Unresolve"
    assert json.loads(ack_button["value"]) == {"organization_id": organization.pk, "alert_group_pk": alert_group.pk}


@pytest.mark.django_db
def test_slack_renderer_invite_action(
    make_organization, make_user, make_alert_receive_channel, make_alert_group, make_alert
):
    organization = make_organization()
    user = make_user(organization=organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={})

    elements = AlertGroupSlackRenderer(alert_group).render_alert_group_attachments()[0]["blocks"][0]["elements"]

    ack_button = elements[2]
    assert ack_button["placeholder"]["text"] == "Invite..."
    assert json.loads(ack_button["options"][0]["value"]) == {
        "organization_id": organization.pk,
        "alert_group_pk": alert_group.pk,
        "user_id": user.pk,
    }


@pytest.mark.django_db
def test_slack_renderer_stop_invite_button(
    make_organization, make_user, make_alert_receive_channel, make_alert_group, make_alert, make_invitation
):
    organization = make_organization()
    user = make_user(organization=organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={})
    invitation = make_invitation(alert_group, user, user)

    stop_inviting_action = AlertGroupSlackRenderer(alert_group).render_alert_group_attachments()[1]["actions"][0]

    assert stop_inviting_action["text"] == f"Stop inviting {user.username}"
    assert json.loads(stop_inviting_action["value"]) == {
        "organization_id": organization.pk,
        "alert_group_pk": alert_group.pk,
        "invitation_id": invitation.pk,
    }


@pytest.mark.django_db
def test_slack_renderer_silence_button(make_organization, make_alert_receive_channel, make_alert_group, make_alert):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={})

    elements = AlertGroupSlackRenderer(alert_group).render_alert_group_attachments()[0]["blocks"][0]["elements"]

    silence_button = elements[3]
    assert silence_button["placeholder"]["text"] == "Silence"

    values = [json.loads(option["value"]) for option in silence_button["options"]]
    assert values == [
        {"organization_id": organization.pk, "alert_group_pk": alert_group.pk, "duration": duration}
        for duration, _ in AlertGroup.SILENCE_DELAY_OPTIONS
    ]


@pytest.mark.django_db
def test_slack_renderer_unsilence_button(make_organization, make_alert_receive_channel, make_alert_group, make_alert):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, silenced=True)
    make_alert(alert_group=alert_group, raw_request_data={})

    elements = AlertGroupSlackRenderer(alert_group).render_alert_group_attachments()[0]["blocks"][0]["elements"]
    unsilence_button = elements[3]

    assert unsilence_button["text"]["text"] == "Unsilence"
    assert json.loads(unsilence_button["value"]) == {
        "organization_id": organization.pk,
        "alert_group_pk": alert_group.pk,
    }


@pytest.mark.django_db
def test_slack_renderer_attach_button(make_organization, make_alert_receive_channel, make_alert_group, make_alert):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, silenced=True)
    make_alert(alert_group=alert_group, raw_request_data={})

    elements = AlertGroupSlackRenderer(alert_group).render_alert_group_attachments()[0]["blocks"][0]["elements"]
    unsilence_button = elements[4]

    assert unsilence_button["text"]["text"] == "Attach to ..."
    assert json.loads(unsilence_button["value"]) == {
        "organization_id": organization.pk,
        "alert_group_pk": alert_group.pk,
    }


@pytest.mark.django_db
def test_slack_renderer_unattach_button(make_organization, make_alert_receive_channel, make_alert_group, make_alert):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)

    root_alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=root_alert_group, raw_request_data={})

    alert_group = make_alert_group(alert_receive_channel, root_alert_group=root_alert_group)
    make_alert(alert_group=alert_group, raw_request_data={})

    unattach_action = AlertGroupSlackRenderer(alert_group).render_alert_group_attachments()[0]["actions"][0]

    assert unattach_action["text"] == "Unattach"
    assert json.loads(unattach_action["value"]) == {
        "organization_id": organization.pk,
        "alert_group_pk": alert_group.pk,
    }


@pytest.mark.django_db
def test_slack_renderer_format_alert_button(
    make_organization, make_alert_receive_channel, make_alert_group, make_alert
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={})

    elements = AlertGroupSlackRenderer(alert_group).render_alert_group_attachments()[0]["blocks"][0]["elements"]

    ack_button = elements[5]
    assert ack_button["text"]["text"] == ":mag: Format Alert"
    assert json.loads(ack_button["value"]) == {"organization_id": organization.pk, "alert_group_pk": alert_group.pk}


@pytest.mark.django_db
def test_slack_renderer_resolution_notes_button(
    make_organization, make_alert_receive_channel, make_alert_group, make_alert
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data={})

    elements = AlertGroupSlackRenderer(alert_group).render_alert_group_attachments()[0]["blocks"][0]["elements"]

    ack_button = elements[6]
    assert ack_button["text"]["text"] == "Add Resolution notes"
    assert json.loads(ack_button["value"]) == {
        "organization_id": organization.pk,
        "alert_group_pk": alert_group.pk,
        "resolution_note_window_action": "edit",
    }
