from apps.slack.slash_command import SlashCommand


def test_parse():
    payload = {
        "command": "/grafana-irm",
        "text": "escalate",
        "trigger_id": "trigger_id",
        "user_id": "user_id",
        "user_name": "user_name",
        "api_app_id": "api_app_id",
    }
    slash_command = SlashCommand.parse(payload)
    assert slash_command.command == "grafana-irm"
    assert slash_command.args == ["escalate"]
    assert slash_command.subcommand == "escalate"
    assert slash_command.is_grafana_command


def test_parse_command_without_subcommand():
    payload = {
        "command": "/escalate",
        "text": "",
        "trigger_id": "trigger_id",
        "user_id": "user_id",
        "user_name": "user_name",
        "api_app_id": "api_app_id",
    }
    slash_command = SlashCommand.parse(payload)
    assert slash_command.command == "escalate"
    assert slash_command.args == []
    assert slash_command.subcommand is None
