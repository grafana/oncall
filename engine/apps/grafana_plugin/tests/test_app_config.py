import sys
from unittest.mock import patch

import pytest
from django.apps import apps
from django.test import override_settings

app_name = "grafana_plugin"


@patch.object(sys, "argv", ["runserver"])
@patch.object(sys, "exit")
@override_settings(OSS_INSTALLATION=True)
@override_settings(SELF_HOSTED_SETTINGS={"GRAFANA_API_URL": None})
@pytest.mark.django_db
def test_it_crashes_the_app_if_the_env_var_is_not_present_for_oss_installations_and_an_org_does_not_exist(
    mocked_sys_exit,
) -> None:
    apps.get_app_config(app_name).ready()
    mocked_sys_exit.assert_called_once()


@patch.object(sys, "argv", ["runserver"])
@patch.object(sys, "exit")
@override_settings(OSS_INSTALLATION=True)
@override_settings(SELF_HOSTED_SETTINGS={"GRAFANA_API_URL": None})
@pytest.mark.django_db
def test_it_doesnt_crash_the_app_if_the_env_var_is_not_present_for_oss_installations_and_an_org_does_exist(
    mocked_sys_exit, make_organization
) -> None:
    make_organization()

    apps.get_app_config(app_name).ready()
    mocked_sys_exit.assert_not_called()


@patch.object(sys, "argv", ["migration"])
@patch.object(sys, "exit")
@override_settings(OSS_INSTALLATION=True)
def test_it_only_checks_when_the_runserver_command_is_concerned(mocked_sys_exit) -> None:
    apps.get_app_config(app_name).ready()
    mocked_sys_exit.assert_not_called()


@patch.object(sys, "argv", ["runserver"])
@patch.object(sys, "exit")
@override_settings(OSS_INSTALLATION=False)
def test_it_ignores_non_oss_installations(mocked_sys_exit) -> None:
    apps.get_app_config(app_name).ready()
    mocked_sys_exit.assert_not_called()
