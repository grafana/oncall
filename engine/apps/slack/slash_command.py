from django.conf import settings

from apps.slack.types.interaction_payloads import SlashCommandPayload


class SlashCommand:
    """
    SlashCommand represents slack slash command.

    Attributes:
    command -- command itself
    args -- list of args passed to command
    Examples:
        /grafana escalate
        SlashCommand(command='grafana', args=['escalate'])
    """

    def __init__(self, command, args):
        # command itself
        self.command = command
        # list of args passed to command
        self.args = args

    @property
    def subcommand(self):
        """
        Return first arg as action subcommand: part of command which defines action
        Example: /grafana escalate -> escalate
        """
        return self.args[0] if len(self.args) > 0 else None

    @staticmethod
    def parse(payload: SlashCommandPayload):
        """
        Parse slack slash command payload and return SlashCommand object
        """
        command = payload["command"].lstrip("/")
        args = payload["text"].split()
        return SlashCommand(command, args)

    @property
    def is_root_command(self):
        return self.command == settings.SLACK_IRM_ROOT_COMMAND
