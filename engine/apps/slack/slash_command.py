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
        Return first arg as subcommand
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
