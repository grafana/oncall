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
    def parse(text: str):
        """
        Parse command text
        """
        parts = text.split()
        command = parts[0].lstrip("/")
        args = parts[1:]
        return SlashCommand(command, args)
