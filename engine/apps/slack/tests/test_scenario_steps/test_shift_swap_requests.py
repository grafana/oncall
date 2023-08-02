import datetime
import json
from unittest.mock import patch

import pytest
import pytz

from apps.schedules import exceptions
from apps.slack.scenarios import shift_swap_requests as scenarios


@pytest.fixture
def setup(make_organization_and_user_with_slack_identities, shift_swap_request_setup):
    def _setup(**kwargs):
        organization, _, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
        ssr, beneficiary, benefactor = shift_swap_request_setup(**kwargs)

        organization = ssr.organization
        organization.slack_team_identity = slack_team_identity
        organization.save()

        return ssr, beneficiary, benefactor, slack_user_identity

    return _setup


@pytest.fixture
def payload():
    def _payload(shift_swap_request_pk):
        return {"actions": [{"value": json.dumps({"shift_swap_request_pk": shift_swap_request_pk})}]}

    return _payload


class TestBaseShiftSwapRequestStep:
    @pytest.mark.django_db
    def test_generate_blocks(self, setup) -> None:
        ssr, beneficiary, _, _ = setup()

        step = scenarios.BaseShiftSwapRequestStep(ssr.organization.slack_team_identity, ssr.organization)
        blocks = step._generate_blocks(ssr)

        assert (
            blocks[0]["text"]["text"]
            == f"Your teammate {beneficiary.get_username_with_slack_verbal()} has submitted a shift swap request."
        )

        accept_button = blocks[2]

        assert accept_button["elements"][0]["text"]["text"] == "✔️ Accept Shift Swap Request"
        assert accept_button["type"] == "actions"

        assert blocks[3]["type"] == "divider"

        context_section = blocks[4]

        assert context_section["type"] == "context"
        assert (
            context_section["elements"][0]["text"]
            == f"👀 View the shift swap within Grafana OnCall by clicking <{ssr.web_link}|here>."
        )

    @patch("apps.schedules.models.ShiftSwapRequest.shifts")
    @pytest.mark.parametrize(
        "shifts,expected_text",
        [
            (
                # shifts start and end on same day
                [
                    {
                        "start": datetime.datetime(2023, 8, 29, 12, 0, 0, 0, pytz.UTC),
                        "end": datetime.datetime(2023, 8, 29, 17, 30, 0, 0, pytz.UTC),
                    },
                    {
                        "start": datetime.datetime(2023, 8, 30, 12, 0, 0, 0, pytz.UTC),
                        "end": datetime.datetime(2023, 8, 30, 17, 30, 0, 0, pytz.UTC),
                    },
                ],
                (
                    "• <!date^1693310400^{date_long_pretty} {time}|2023-08-29 12:00 (UTC)> - <!date^1693330200^{time}|2023-08-29 17:30 (UTC)>\n"
                    "• <!date^1693396800^{date_long_pretty} {time}|2023-08-30 12:00 (UTC)> - <!date^1693416600^{time}|2023-08-30 17:30 (UTC)>\n"
                ),
            ),
            (
                # shifts start and end on different days
                [
                    {
                        "start": datetime.datetime(2023, 8, 29, 18, 0, 0, 0, pytz.UTC),
                        "end": datetime.datetime(2023, 8, 30, 6, 30, 0, 0, pytz.UTC),
                    },
                    {
                        "start": datetime.datetime(2023, 9, 1, 18, 0, 0, 0, pytz.UTC),
                        "end": datetime.datetime(2023, 9, 2, 6, 30, 0, 0, pytz.UTC),
                    },
                ],
                (
                    "• <!date^1693332000^{date_long_pretty} {time}|2023-08-29 18:00 (UTC)> - <!date^1693377000^{date_long_pretty} {time}|2023-08-30 06:30 (UTC)>\n"
                    "• <!date^1693591200^{date_long_pretty} {time}|2023-09-01 18:00 (UTC)> - <!date^1693636200^{date_long_pretty} {time}|2023-09-02 06:30 (UTC)>\n"
                ),
            ),
        ],
    )
    @pytest.mark.django_db
    def test_generate_blocks_shift_details(self, mock_shifts, setup, shifts, expected_text) -> None:
        mock_shifts.return_value = shifts
        ssr, _, _, _ = setup()

        step = scenarios.BaseShiftSwapRequestStep(ssr.organization.slack_team_identity, ssr.organization)
        blocks = step._generate_blocks(ssr)

        assert blocks[1]["text"]["text"] == f"*📅 Shift Details*:\n\n{expected_text}"

    @pytest.mark.django_db
    def test_generate_blocks_ssr_has_description(self, setup) -> None:
        description = "asdlfkjalkjqwelkrjqwlkerj"
        ssr, _, _, _ = setup(description=description)

        step = scenarios.BaseShiftSwapRequestStep(ssr.organization.slack_team_identity, ssr.organization)
        blocks = step._generate_blocks(ssr)

        assert blocks[2]["text"]["text"] == f"*📝 Description*: {description}"

    @pytest.mark.django_db
    def test_generate_blocks_ssr_is_deleted(self, setup) -> None:
        ssr, _, _, _ = setup()
        ssr.delete()

        step = scenarios.BaseShiftSwapRequestStep(ssr.organization.slack_team_identity, ssr.organization)
        blocks = step._generate_blocks(ssr)

        assert blocks[2]["text"]["text"] == "*Update*: this shift swap request has been deleted."

    @pytest.mark.django_db
    def test_generate_blocks_ssr_is_taken(self, setup) -> None:
        ssr, _, benefactor, _ = setup()
        ssr.benefactor = benefactor
        ssr.save()

        step = scenarios.BaseShiftSwapRequestStep(ssr.organization.slack_team_identity, ssr.organization)
        blocks = step._generate_blocks(ssr)

        assert (
            blocks[2]["text"]["text"]
            == f"*Update*: {benefactor.get_username_with_slack_verbal()} has taken the shift swap."
        )

    @patch("apps.slack.scenarios.shift_swap_requests.BaseShiftSwapRequestStep._generate_blocks")
    @pytest.mark.django_db
    def test_create_message(self, mock_generate_blocks, setup) -> None:
        ts = "12345.67"

        ssr, _, _, _ = setup()
        organization = ssr.organization
        slack_team_identity = organization.slack_team_identity

        step = scenarios.BaseShiftSwapRequestStep(slack_team_identity, organization)

        with patch.object(step, "_slack_client") as mock_slack_client:
            mock_slack_client.api_call.return_value = {"ts": ts}

            slack_message = step.create_message(ssr)

            mock_generate_blocks.assert_called_once_with(ssr)
            mock_slack_client.api_call.assert_called_once_with(
                "chat.postMessage", channel=ssr.slack_channel_id, blocks=mock_generate_blocks.return_value
            )

        assert slack_message.slack_id == ts
        assert slack_message.organization == organization
        assert slack_message.channel_id == ssr.slack_channel_id
        assert slack_message._slack_team_identity == slack_team_identity

    @patch("apps.slack.scenarios.shift_swap_requests.BaseShiftSwapRequestStep._generate_blocks")
    @pytest.mark.django_db
    def test_update_message(self, mock_generate_blocks, setup, make_slack_message) -> None:
        ts = "12345.67"

        ssr, _, _, _ = setup()
        organization = ssr.organization
        slack_team_identity = organization.slack_team_identity

        slack_message = make_slack_message(alert_group=None, organization=organization, slack_id=ts)
        ssr.slack_message = slack_message
        ssr.save()

        step = scenarios.BaseShiftSwapRequestStep(slack_team_identity, organization)

        with patch.object(step, "_slack_client") as mock_slack_client:
            step.update_message(ssr)

            mock_generate_blocks.assert_called_once_with(ssr)
            mock_slack_client.api_call.assert_called_once_with(
                "chat.update", channel=ssr.slack_channel_id, ts=ts, blocks=mock_generate_blocks.return_value
            )


class TestAcceptShiftSwapRequestStep:
    @pytest.mark.django_db
    def test_process_scenario(self, setup, payload) -> None:
        ssr, _, benefactor, slack_user_identity = setup()
        event_payload = payload(ssr.pk)

        organization = ssr.organization
        slack_team_identity = organization.slack_team_identity

        step = scenarios.AcceptShiftSwapRequestStep(slack_team_identity, organization, benefactor)

        with patch.object(step, "update_message") as mock_update_message:
            step.process_scenario(slack_user_identity, slack_team_identity, event_payload)

            ssr.refresh_from_db()
            assert ssr.benefactor == benefactor
            assert ssr.is_taken is True

            mock_update_message.assert_called_once_with(ssr)

    @patch("apps.schedules.models.shift_swap_request.ShiftSwapRequest.take")
    @pytest.mark.django_db
    def test_process_scenario_ssr_does_not_exist(self, mock_take, setup, payload) -> None:
        event_payload = payload("12345")
        ssr, _, benefactor, slack_user_identity = setup()

        organization = ssr.organization
        slack_team_identity = organization.slack_team_identity

        step = scenarios.AcceptShiftSwapRequestStep(slack_team_identity, organization, benefactor)

        with patch.object(step, "update_message") as mock_update_message:
            step.process_scenario(slack_user_identity, slack_team_identity, event_payload)

            assert ssr.is_taken is False
            assert ssr.benefactor is None

            mock_take.assert_not_called()
            mock_update_message.assert_not_called()

    @patch(
        "apps.schedules.models.shift_swap_request.ShiftSwapRequest.take",
        side_effect=exceptions.BeneficiaryCannotTakeOwnShiftSwapRequest,
    )
    @pytest.mark.django_db
    def test_process_scenario_cannot_take_own_ssr(self, mock_take, setup, payload) -> None:
        ssr, beneficiary, _, slack_user_identity = setup()
        event_payload = payload(ssr.pk)

        organization = ssr.organization
        slack_team_identity = organization.slack_team_identity

        step = scenarios.AcceptShiftSwapRequestStep(slack_team_identity, organization, beneficiary)

        with patch.object(step, "update_message") as mock_update_message:
            with patch.object(step, "open_warning_window") as mock_open_warning_window:
                step.process_scenario(slack_user_identity, slack_team_identity, event_payload)

                mock_take.assert_called_once_with(beneficiary)
                mock_open_warning_window.assert_called_once_with(
                    event_payload, "A shift swap request cannot be created and taken by the same user"
                )
                mock_update_message.assert_not_called()

    @patch(
        "apps.schedules.models.shift_swap_request.ShiftSwapRequest.take",
        side_effect=exceptions.ShiftSwapRequestNotOpenForTaking,
    )
    @pytest.mark.django_db
    def test_process_scenario_ssr_is_not_open_for_taking(self, mock_take, setup, payload) -> None:
        ssr, _, benefactor, slack_user_identity = setup()
        event_payload = payload(ssr.pk)

        organization = ssr.organization
        slack_team_identity = organization.slack_team_identity

        step = scenarios.AcceptShiftSwapRequestStep(slack_team_identity, organization, benefactor)

        with patch.object(step, "update_message") as mock_update_message:
            with patch.object(step, "open_warning_window") as mock_open_warning_window:
                step.process_scenario(slack_user_identity, slack_team_identity, event_payload)

                mock_take.assert_called_once_with(benefactor)
                mock_open_warning_window.assert_called_once_with(
                    event_payload, "The shift swap request is not in a state which allows it to be taken"
                )
                mock_update_message.assert_not_called()
