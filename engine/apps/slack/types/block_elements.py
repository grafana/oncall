"""
[Documentation](https://api.slack.com/reference/block-kit/block-elements)
"""

import typing

from .common import Style
from .composition_objects import (
    CompositionObjectConfirm,
    CompositionObjectOption,
    CompositionObjectPlainText,
    CompositionObjectText,
)


class _BaseBlockElement(typing.TypedDict):
    action_id: str
    """
        An identifier for this action. You can use this when you receive an interaction payload to
        [identify the source of the action](https://api.slack.com/interactivity/handling#payloads). Should be unique among
        all other `action_id`s in the containing block. Maximum length for this field is 255 characters.
        """


class BlockElement:
    class Button(_BaseBlockElement):
        """
        An interactive component that inserts a button. The button can be a trigger for anything from opening
        a simple link to starting a complex workflow.

        [Documentation](https://api.slack.com/reference/block-kit/block-elements#button)
        """

        type: typing.Literal["button"]
        """
        The type of element. In this case `type` is always `button`.
        """

        text: CompositionObjectText
        """
        A [text object](https://api.slack.com/reference/block-kit/composition-objects#text) that defines the button's text.

        Can only be of `type: plain_text`. `text` may truncate with ~30 characters. Maximum length for the `text` in this
        field is 75 characters.
        """

        style: Style | None
        """
        Decorates buttons with alternative visual color schemes. Use this option with restraint.

        `primary` gives buttons a green outline and text, ideal for affirmation or confirmation actions. `primary` should
        only be used for one button within a set.

        `danger` gives buttons a red outline and text, and should be used when the action is destructive. Use `danger` even more sparingly than `primary`.

        If you don't include this field, the `default` button style will be used.
        """

    class CheckboxGroup(_BaseBlockElement):
        """
        A checkbox group that allows a user to choose multiple items from a list of possible options.

        [Documentation](https://api.slack.com/reference/block-kit/block-elements#checkboxes)
        """

        type: typing.Literal["checkboxes"]
        """
        The type of element. In this case `type` is always `checkboxes`.
        """

        options: typing.List[CompositionObjectOption]
        """
        An array of [option objects](https://api.slack.com/reference/block-kit/composition-objects#option).
        A maximum of 10 options are allowed.
        """

        initial_options: typing.Optional[typing.List[CompositionObjectOption]]
        """
        An array of [option objects](https://api.slack.com/reference/block-kit/composition-objects#option) that exactly
        matches one or more of the options within `options`. These options will be selected when the checkbox group
        initially loads.
        """

        confirm: typing.Optional[CompositionObjectConfirm]
        """
        A [confirm object](https://api.slack.com/reference/block-kit/composition-objects#confirm) that defines an optional
        confirmation dialog that appears after clicking one of the checkboxes in this element.
        """

        focus_on_load: typing.Optional[bool]
        """
        Indicates whether the element will be set to auto focus within the
        [view object](https://api.slack.com/reference/surfaces/views). Only one element can be set to `true`. Defaults to
        `false`.
        """

    class DatePicker(_BaseBlockElement):
        """
        An element which lets users easily select a date from a calendar style UI.

        [Documentation](https://api.slack.com/reference/block-kit/block-elements#datepicker)
        """

        type: typing.Literal["datepicker"]
        """
        The type of element. In this case `type` is always `datepicker`.
        """

        initial_date: str
        """
        The initial date that is selected when the element is loaded. This should be in the format `YYYY-MM-DD`.
        """

        confirm: CompositionObjectConfirm
        """
        A [confirm object](https://api.slack.com/reference/block-kit/composition-objects#confirm) that defines an
        optional confirmation dialog that appears after a menu item is selected.
        """

        focus_on_load: bool
        """
        Indicates whether the element will be set to auto focus within the
        [view object](https://api.slack.com/reference/surfaces/views).

        Only one element can be set to `true`. Defaults to `false`.
        """

        placeholder: CompositionObjectPlainText
        """
        A [plain_text only text object](https://api.slack.com/reference/block-kit/composition-objects#text) that
        defines the placeholder text shown on the datepicker.

        Maximum length for the `text` in this field is 150 characters.
        """

    class Image(typing.TypedDict):
        """
        An element to insert an image as part of a larger block of content.

        If you want a block with only an image in it, you're looking for the
        [image block](https://api.slack.com/reference/block-kit/blocks#image).

        [Documentation](https://api.slack.com/reference/block-kit/block-elements#image)
        """

        type: typing.Literal["button"]
        """
        The type of element. In this case `type` is always `button`.
        """

        image_url: str
        """
        The URL of the image to be displayed.
        """

        alt_text: str
        """
        A plain-text summary of the image. This should not contain any markup.
        """

    class OverflowMenu(_BaseBlockElement):
        """
        This is like a cross between a button and a select menu - when a user clicks on this overflow button, they will
        be presented with a list of options to choose from. Unlike the select menu, there is no typeahead field, and
        the button always appears with an ellipsis ("…") rather than customizable text.

        As such, it is usually used if you want a more compact layout than a select menu, or to supply a list of less
        visually important actions after a row of buttons. You can also specify simple URL links as overflow menu
        options, instead of actions.

        [Documentation](https://api.slack.com/reference/block-kit/block-elements#overflow)
        """

        type: typing.Literal["overflow"]
        """
        The type of element. In this case `type` is always `overflow`.
        """

        options: typing.List[CompositionObjectOption]
        """
        An array of up to five [option objects](https://api.slack.com/reference/block-kit/composition-objects#option)
        to display in the menu.
        """

        confirm: CompositionObjectConfirm
        """
        A [confirm object](https://api.slack.com/reference/block-kit/composition-objects#confirm) that defines an
        optional confirmation dialog that appears after a menu item is selected.
        """

    class Select:
        class Channels(_BaseBlockElement):
            """
            This select menu will populate its options with a list of public channels visible to the current user in
            the active workspace.

            [Documentation](https://api.slack.com/reference/block-kit/block-elements#channels_select)
            """

            type: typing.Literal["channels_select"]
            """
            The type of element. In this case `type` is always `channels_select`
            """

        class Conversations(_BaseBlockElement):
            """
            This select menu will populate its options with a list of public and private channels, DMs, and MPIMs
            visible to the current user in the active workspace.

            [Documentation](https://api.slack.com/reference/block-kit/block-elements#conversations_select)
            """

            type: typing.Literal["conversations_select"]
            """
            The type of element. In this case `type` is always `conversations_select`
            """

        class External(_BaseBlockElement):
            """
            This select menu will load its options from an external data source, allowing for a dynamic list of options.

            [Documentation](https://api.slack.com/reference/block-kit/block-elements#external_select)
            """

            type: typing.Literal["external_select"]
            """
            The type of element. In this case `type` is always `external_select`
            """

        class Static(_BaseBlockElement):
            """
            This is the simplest form of select menu, with a static list of options passed in when defining the element.

            [Documentation](https://api.slack.com/reference/block-kit/block-elements#static_select)
            """

            type: typing.Literal["static_select"]
            """
            The type of element. In this case `type` is always `static_select`
            """

        class Users(_BaseBlockElement):
            """
            This select menu will populate its options with a list of Slack users visible to the current user in the active workspace.

            [Documentation](https://api.slack.com/reference/block-kit/block-elements#users_select)
            """

            type: typing.Literal["users_select"]
            """
            The type of element. In this case `type` is always `users_select`
            """

        Any = Channels | Conversations | External | Static | Users

    Any = Button | CheckboxGroup | DatePicker | Image | OverflowMenu | Select.Any


__all__ = [
    "BlockElement",
]
