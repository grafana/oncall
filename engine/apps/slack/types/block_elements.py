"""
[Documentation](https://api.slack.com/reference/block-kit/block-elements)
"""

import typing

from .common import Style
from .composition_objects import Confirm, Option, Text


class BlockElement:
    class _BaseBlockElement(typing.TypedDict):
        action_id: str
        """
        An identifier for this action. You can use this when you receive an interaction payload to
        [identify the source of the action](https://api.slack.com/interactivity/handling#payloads). Should be unique among
        all other `action_id`s in the containing block. Maximum length for this field is 255 characters.
        """

    class Button(_BaseBlockElement):
        """
        [Documentation](https://api.slack.com/reference/block-kit/block-elements#button)
        """

        type: typing.Literal["button"]
        """
        The type of element. In this case `type` is always `button`.
        """

        text: Text
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
        [Documentation](https://api.slack.com/reference/block-kit/block-elements#checkboxes)
        """

        type: typing.Literal["checkboxes"]
        """
        The type of element. In this case `type` is always `checkboxes`.
        """

        options: typing.List[Option]
        """
        An array of [option objects](https://api.slack.com/reference/block-kit/composition-objects#option).
        A maximum of 10 options are allowed.
        """

        initial_options: typing.Optional[typing.List[Option]]
        """
        An array of [option objects](https://api.slack.com/reference/block-kit/composition-objects#option) that exactly
        matches one or more of the options within `options`. These options will be selected when the checkbox group
        initially loads.
        """

        confirm: typing.Optional[Confirm]
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

    Any = Button | CheckboxGroup
