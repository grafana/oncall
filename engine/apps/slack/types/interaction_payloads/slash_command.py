"""
[Documentation](https://api.slack.com/interactivity/slash-commands#app_command_handling)
"""

import typing


class SlashCommandPayload(typing.TypedDict):
    """
    [Documentation](https://api.slack.com/interactivity/slash-commands#app_command_handling)
    """

    command: str
    """
    The command that was typed in to trigger this request.

    This value can be useful if you want to use a single Request URL to service multiple Slash Commands, as it lets you
    tell them apart.
    """

    text: str
    """
    This is the part of the Slash Command after the command itself, and it can contain absolutely anything that the
    user might decide to type. It is common to use this text parameter to provide extra context for the command.

    You can prompt users to adhere to a particular format by showing them in the
    [Usage Hint field when creating a command](https://api.slack.com/interactivity/slash-commands#app_command_handling:~:text=tell%20them%20apart.-,text,them%20in%20the%20Usage%20Hint%20field%20when%20creating%20a%20command.,-response_url).
    """  # noqa: E501

    trigger_id: str
    """
    A short-lived ID that will let your app open [a modal](https://api.slack.com/surfaces/modals).
    """

    user_id: str
    """
    The ID of the user who triggered the command.
    """

    user_name: str
    """
    The plain text name of the user who triggered the command. As [above](https://api.slack.com/interactivity/slash-commands#escaping_users_warning),
    do not rely on this field as it is being [phased out](https://api.slack.com/interactivity/slash-commands#app_command_handling:~:text=it%20is%20being-,phased%20out,-%2C%20use%20the), use the `user_id` instead.
    """  # noqa: E501

    api_app_id: str
    """
    Your Slack app's unique identifier. Use this in conjunction with [request signing](https://api.slack.com/authentication/verifying-requests-from-slack)
    to verify context for inbound requests.
    """
