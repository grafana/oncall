from apps.slack.slash_command import SlashCommand


def test_parse():
    text = "/grafana escalate"
    slash_command = SlashCommand.parse(text)
    assert slash_command.command == "grafana"
    assert slash_command.args == ["escalate"]


def test_parse_command_without_subcommand():
    text = "/escalate"
    slash_command = SlashCommand.parse(text)
    assert slash_command.command == "escalate"
    assert slash_command.args == []
    assert slash_command.subcommand is None


def test_subcommand():
    command = "grafana"
    args = ["escalate"]
    slash_command = SlashCommand(command, args)
    assert slash_command.subcommand == "escalate"
