import typing

from .common import EventType, PayloadType

if typing.TYPE_CHECKING:
    from apps.slack.scenarios.scenario_step import ScenarioStep
    from apps.slack.types import BlockActionType, InteractiveMessageActionType


class ScenarioRoute:
    class _Base(typing.TypedDict):
        step: "ScenarioStep"

    class BlockActionsScenarioRoute(_Base):
        payload_type: typing.Literal[PayloadType.BLOCK_ACTIONS]
        block_action_type: "BlockActionType"
        block_action_id: str

    class EventCallbackScenarioRoute(_Base):
        payload_type: typing.Literal[PayloadType.EVENT_CALLBACK]
        event_type: EventType

    class EventCallbackChannelMessageScenarioRoute(EventCallbackScenarioRoute):
        """
        NOTE: the reason why we need to subclass `EventCallbackScenarioRoute` is because in Python 3.11 there is currently
        no way to specify keys as optional in a `typing.TypedDict`. See [PEP-692](https://peps.python.org/pep-0692/) which
        will implement this typing feature in Python 3.12.

        When we upgrade to 3.12 we should update this type.
        """

        message_channel_type: typing.Literal[EventType.MESSAGE_CHANNEL]

    class InteractiveMessageScenarioRoute(_Base):
        payload_type: typing.Literal[PayloadType.INTERACTIVE_MESSAGE]
        action_type: "InteractiveMessageActionType"
        action_name: str

    class MessageActionScenarioRoute(_Base):
        payload_type: typing.Literal[PayloadType.SLASH_COMMAND]
        message_action_callback_id: typing.List[str]

    class SlashCommandScenarioRoute(_Base):
        payload_type: typing.Literal[PayloadType.SLASH_COMMAND]
        command_name: typing.List[str]

    class ViewSubmissionScenarioRoute(_Base):
        payload_type: typing.Literal[PayloadType.VIEW_SUBMISSION]
        view_callback_id: str

    RoutingStep = (
        BlockActionsScenarioRoute
        | EventCallbackScenarioRoute
        | EventCallbackChannelMessageScenarioRoute
        | InteractiveMessageScenarioRoute
        | MessageActionScenarioRoute
        | SlashCommandScenarioRoute
        | ViewSubmissionScenarioRoute
    )
    RoutingSteps = typing.List[RoutingStep]
