from unittest.mock import patch

from django.test import override_settings

from common.recaptcha.recaptcha_v3 import check_recaptcha_v3

action = "test_action"
score = 0.9
value = "test_value"
client_ip = "192.168.1.1"


@override_settings(RECAPTCHA_V3_ENABLED=True)
def test_captcha_v3_fails():
    with patch(
        "common.recaptcha.recaptcha_v3._submit_recaptcha_v3",
        return_value={"success": False, "error-codes": ["invalid-input-secret"]},
    ):
        valid = check_recaptcha_v3(value, action, score, client_ip)

        assert not valid


@override_settings(RECAPTCHA_V3_ENABLED=True)
def test_captcha_v3_fails_actions_dont_match():
    with patch(
        "common.recaptcha.recaptcha_v3._submit_recaptcha_v3",
        return_value={
            "success": True,
            "challenge_ts": "2023-03-02T14:44:18Z",
            "hostname": "localhost",
            "score": 0.9,
            "action": "not_the_action_you_are_looking_for",
        },
    ):
        valid = check_recaptcha_v3(value, action, score, client_ip)

        assert not valid


@override_settings(RECAPTCHA_V3_ENABLED=True)
def test_captcha_v3_fails_score_too_low():
    with patch(
        "common.recaptcha.recaptcha_v3._submit_recaptcha_v3",
        return_value={
            "success": True,
            "challenge_ts": "2023-03-02T14:44:18Z",
            "hostname": "localhost",
            "score": 0.8,
            "action": "not_the_action_you_are_looking_for",
        },
    ):
        valid = check_recaptcha_v3(value, action, score, client_ip)

        assert not valid


@override_settings(RECAPTCHA_V3_ENABLED=True)
@override_settings(RECAPTCHA_V3_HOSTNAME_VALIDATION=True)
def test_captcha_v3_fails_invalid_hostname():
    hostname = "localhost"
    with patch(
        "common.recaptcha.recaptcha_v3._submit_recaptcha_v3",
        return_value={
            "success": True,
            "challenge_ts": "2023-03-02T14:44:18Z",
            "hostname": "not_the_hostname_you_are_looking_for",
            "score": 0.8,
            "action": action,
        },
    ):
        valid = check_recaptcha_v3(value, action, score, client_ip, hostname)

        assert not valid


@override_settings(RECAPTCHA_V3_ENABLED=True)
def test_captcha_v3_valid():
    with patch(
        "common.recaptcha.recaptcha_v3._submit_recaptcha_v3",
        return_value={
            "success": True,
            "challenge_ts": "2023-03-02T14:44:18Z",
            "hostname": "localhost",
            "score": 1.0,
            "action": action,
        },
    ):
        valid = check_recaptcha_v3(value, action, score, client_ip)

        assert valid


@override_settings(RECAPTCHA_V3_ENABLED=True)
def test_captcha_v3_valid_with_hostname_validation():
    hostname = "localhost"
    with patch(
        "common.recaptcha.recaptcha_v3._submit_recaptcha_v3",
        return_value={
            "success": True,
            "challenge_ts": "2023-03-02T14:44:18Z",
            "hostname": hostname,
            "score": 1.0,
            "action": action,
        },
    ):
        valid = check_recaptcha_v3(value, action, score, client_ip, hostname)

        assert valid
